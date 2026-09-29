"""Atomic append-only curation apply and validator rollback."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import uuid
from collections import defaultdict
from contextlib import contextmanager
from datetime import UTC, date, datetime
from pathlib import Path
from time import monotonic, sleep

from ..sdk.v1.models import (
    InvalidRequestError, KnowledgeApplyResult, KnowledgeCurationError,
    KnowledgeProposalValidation, KnowledgeRuleProposal, KnowledgeValidatorResult,
)
from . import common
from .common import (
    KnowledgeValidatorError, _FRONTMATTER, _HEADING, _MAX_SECTION_CHARS,
    _MAX_SOURCE_CHARS, _RULE_ID, _UPDATED, _VALIDATOR_IDS, _sha256,
)


class ApplyMixin:
    @staticmethod
    def _updated_page(text: str, sections: list[str], updated_on: str) -> str:
        match = _FRONTMATTER.match(text)
        if match is None:
            raise KnowledgeCurationError(
                "target rules page has no valid YAML frontmatter boundary"
            )
        frontmatter = match.group("body")
        updated_fields = list(_UPDATED.finditer(frontmatter))
        if len(updated_fields) != 1:
            raise KnowledgeCurationError(
                "target rules page must have exactly one updated frontmatter field"
            )
        field = updated_fields[0]
        replaced = (
            frontmatter[:field.start()]
            + f"updated: {updated_on}"
            + frontmatter[field.end():]
        )
        content = text[:match.start("body")] + replaced + text[match.end("body"):]
        if not content.endswith(("\n", "\r")):
            content += "\n"
        for section in sections:
            content += "\n" + section.rstrip() + "\n"
        return content

    @staticmethod
    def _normalize_date(updated_on: str | date | None) -> str:
        if updated_on is None:
            return datetime.now(UTC).date().isoformat()
        if isinstance(updated_on, date):
            return updated_on.isoformat()
        value = str(updated_on).strip()
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise InvalidRequestError("updated_on must be an ISO YYYY-MM-DD date") from exc
        if parsed.isoformat() != value:
            raise InvalidRequestError("updated_on must be an ISO YYYY-MM-DD date")
        return value

    @staticmethod
    def _atomic_write(path: Path, data: bytes) -> None:
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            temporary.write_bytes(data)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    @contextmanager
    def _process_lock(self):
        """Serialize writers across Curator instances and host processes."""
        if common.fcntl is None:
            raise KnowledgeCurationError(
                "cross-process file locking is unavailable; apply refused"
            )
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self._lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        deadline = monotonic() + self.lock_timeout_seconds
        try:
            while True:
                try:
                    common.fcntl.flock(descriptor, common.fcntl.LOCK_EX | common.fcntl.LOCK_NB)
                    break
                except BlockingIOError as exc:
                    if monotonic() >= deadline:
                        raise KnowledgeCurationError(
                            "knowledge curator writer lock timed out"
                        ) from exc
                    sleep(0.05)
            try:
                yield
            finally:
                common.fcntl.flock(descriptor, common.fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    def _validator_path(self, validator_id: str) -> Path | None:
        path = self._workspace / validator_id
        if path.is_symlink() or not path.is_file():
            return None
        try:
            path.resolve().relative_to(self._workspace)
        except ValueError:
            return None
        return path

    def _run_validator(self, validator_id: str) -> KnowledgeValidatorResult:
        path = self._validator_path(validator_id)
        if path is None:
            return KnowledgeValidatorResult(
                validator_id=validator_id,
                passed=False,
                status="missing",
                returncode=None,
                output="validator is missing or not a contained regular file",
            )
        try:
            completed = subprocess.run(
                [sys.executable, validator_id],
                cwd=self._workspace,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=self.validator_timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return KnowledgeValidatorResult(
                validator_id=validator_id,
                passed=False,
                status="timeout",
                returncode=None,
                output="validator timed out",
            )
        except OSError as exc:
            return KnowledgeValidatorResult(
                validator_id=validator_id,
                passed=False,
                status="error",
                returncode=None,
                output=f"validator could not run ({type(exc).__name__})",
            )
        output = (completed.stdout + completed.stderr).strip()
        output = output.replace(str(self._workspace), "<workspace>")[-4000:]
        return KnowledgeValidatorResult(
            validator_id=validator_id,
            passed=completed.returncode == 0,
            status="passed" if completed.returncode == 0 else "failed",
            returncode=completed.returncode,
            output=output,
        )

    def _failure(
        self,
        *,
        batch_id: str,
        attempted: int,
        document_ids: tuple[str, ...],
        updated_on: str,
        validators: tuple[KnowledgeValidatorResult, ...],
        rolled_back: bool,
        accepted_indexes: tuple[int, ...],
        rejected_indexes: tuple[int, ...],
    ) -> KnowledgeValidatorError:
        result = KnowledgeApplyResult(
            batch_id=batch_id,
            success=False,
            attempted=attempted,
            applied=0,
            accepted_indexes=accepted_indexes,
            rejected_indexes=rejected_indexes,
            updated_document_ids=document_ids,
            updated_on=updated_on,
            validators=validators,
            rolled_back=rolled_back,
        )
        failed = validators[-1]
        return KnowledgeValidatorError(
            f"knowledge validator failed: {failed.validator_id} ({failed.status})",
            result,
        )

    def apply(
        self,
        validation: KnowledgeProposalValidation,
        *,
        updated_on: str | date | None = None,
    ) -> KnowledgeApplyResult:
        """Append accepted sections, gate with both validators, rollback on fail."""
        applied_on = self._normalize_date(updated_on)
        proposals = validation.accepted
        accepted_indexes = tuple(proposal.input_index for proposal in proposals)
        rejected_indexes = tuple(item.index for item in validation.rejected)
        attempted = len(accepted_indexes) + len(rejected_indexes)
        if not proposals:
            return KnowledgeApplyResult(
                batch_id=validation.batch_id,
                success=True,
                attempted=attempted,
                applied=0,
                accepted_indexes=(),
                rejected_indexes=rejected_indexes,
                updated_document_ids=(),
                updated_on=applied_on,
                validators=(),
                rolled_back=False,
            )

        grouped: dict[str, list[KnowledgeRuleProposal]] = defaultdict(list)
        allowed_catalog = set(self.catalog(validation.repository))
        seen_indexes: set[int] = set()
        for proposal in proposals:
            heading = proposal.section_markdown.splitlines()[0]
            heading_match = _HEADING.match(heading)
            expected_proposal_id = self._proposal_id(
                batch_id=validation.batch_id,
                repository=validation.repository,
                input_index=proposal.input_index,
                page=proposal.page_document_id,
                rule_id=proposal.rule_id,
                section=proposal.section_markdown,
                sources=proposal.sources,
                page_sha256=proposal.page_sha256,
            )
            if (
                proposal.input_index < 0
                or proposal.input_index in seen_indexes
                or proposal.page_document_id not in allowed_catalog
                or not _RULE_ID.fullmatch(proposal.rule_id)
                or heading_match is None
                or heading_match.group("rule") != proposal.rule_id
                or len(re.findall(
                    r"^##\s+", proposal.section_markdown, re.MULTILINE
                )) != 1
                or not 80 <= len(proposal.section_markdown) <= _MAX_SECTION_CHARS
                or self._repeated_section_rule_id(proposal.section_markdown)

                or not proposal.sources
                or len(proposal.sources) > 10
                or any(
                    not source or len(source) > _MAX_SOURCE_CHARS
                    for source in proposal.sources
                )
                or proposal.proposal_id != expected_proposal_id
            ):
                raise KnowledgeCurationError(
                    "accepted proposal failed apply-time integrity validation"
                )
            seen_indexes.add(proposal.input_index)
            grouped[proposal.page_document_id].append(proposal)
        document_ids = tuple(sorted(grouped))

        with self._apply_lock, self._process_lock():
            # Validation ran without the lock: a batch validated alongside
            # this one may have landed the same new ID on ANOTHER page
            # since, which the target-page hash below cannot notice.
            # Re-check tree-wide under the lock, before any write; a
            # change to the target page itself is the hash check's job.
            existing_ids = self._existing_rule_ids()
            for proposal in proposals:
                for heading_id in self._section_rule_ids(
                    proposal.section_markdown
                ):
                    owner = existing_ids.get(heading_id)
                    if owner is not None and owner != proposal.page_document_id:
                        raise KnowledgeCurationError(
                            f"rule_id {heading_id} already exists on {owner}; "
                            "revalidate the batch against the current tree"
                        )


            snapshots: dict[str, bytes] = {}
            rendered: dict[str, bytes] = {}

            for document_id in document_ids:
                path = self._document_path(document_id)
                original = path.read_bytes()
                proposals_for_page = grouped[document_id]
                expected_hashes = {
                    proposal.page_sha256 for proposal in proposals_for_page
                }
                if expected_hashes != {_sha256(original)}:
                    raise KnowledgeCurationError(
                        f"target page changed after validation: {document_id}"
                    )
                seen_ids: set[str] = set()
                page_text = original.decode("utf-8")
                for proposal in proposals_for_page:
                    section_ids = self._section_rule_ids(
                        proposal.section_markdown
                    )
                    if (
                        not _RULE_ID.fullmatch(proposal.rule_id)
                        or any(
                            heading_id in seen_ids
                            or self._rule_exists(page_text, heading_id)
                            for heading_id in section_ids
                        )
                    ):
                        raise KnowledgeCurationError(
                            f"proposal is no longer append-safe: {document_id}"
                        )
                    seen_ids.update(section_ids)

                snapshots[document_id] = original
                rendered[document_id] = self._updated_page(
                    original.decode("utf-8"),
                    [proposal.section_markdown for proposal in proposals_for_page],
                    applied_on,
                ).encode("utf-8")

            missing_results = tuple(
                result
                for validator_id in _VALIDATOR_IDS
                if not (result := self._run_validator_preflight(validator_id)).passed
            )
            if missing_results:
                raise self._failure(
                    batch_id=validation.batch_id,
                    attempted=attempted,
                    document_ids=document_ids,
                    updated_on=applied_on,
                    validators=missing_results,
                    rolled_back=False,
                    accepted_indexes=accepted_indexes,
                    rejected_indexes=rejected_indexes,
                )

            try:
                for document_id in document_ids:
                    self._atomic_write(
                        self._document_path(document_id), rendered[document_id]
                    )
            except OSError as exc:
                for document_id, original in snapshots.items():
                    self._atomic_write(self._document_path(document_id), original)
                raise KnowledgeCurationError(
                    f"could not apply knowledge batch ({type(exc).__name__}); "
                    "target pages were restored"
                ) from exc

            validator_results: list[KnowledgeValidatorResult] = []
            for validator_id in _VALIDATOR_IDS:
                result = self._run_validator(validator_id)
                validator_results.append(result)
                if not result.passed:
                    for document_id, original in snapshots.items():
                        self._atomic_write(self._document_path(document_id), original)
                    raise self._failure(
                        batch_id=validation.batch_id,
                        attempted=attempted,
                        document_ids=document_ids,
                        updated_on=applied_on,
                        validators=tuple(validator_results),
                        rolled_back=True,
                        accepted_indexes=accepted_indexes,
                        rejected_indexes=rejected_indexes,
                    )

            return KnowledgeApplyResult(
                batch_id=validation.batch_id,
                success=True,
                attempted=attempted,
                applied=len(proposals),
                accepted_indexes=accepted_indexes,
                rejected_indexes=rejected_indexes,
                updated_document_ids=document_ids,
                updated_on=applied_on,
                validators=tuple(validator_results),
                rolled_back=False,
            )

    def _run_validator_preflight(
        self, validator_id: str
    ) -> KnowledgeValidatorResult:
        if self._validator_path(validator_id) is None:
            return KnowledgeValidatorResult(
                validator_id=validator_id,
                passed=False,
                status="missing",
                returncode=None,
                output="validator is missing or not a contained regular file",
            )
        return KnowledgeValidatorResult(
            validator_id=validator_id,
            passed=True,
            status="ready",
            returncode=None,
            output="",
        )
