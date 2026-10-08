"""Atomic append-only curation apply and validator rollback."""

from __future__ import annotations

from ..persistence import atomic_write_bytes as _atomic_write

import os
import subprocess
import sys
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
from .catalog import catalog, document_path
from .common import (
    KnowledgeValidatorError, _FRONTMATTER, _UPDATED, _VALIDATOR_IDS, _sha256,
)
from .proposals import (
    _proposal_id, _repeated_section_rule_id,
    _section_rule_ids, existing_rule_ids, section_error,
)
from .lifecycle import first_taken_rule_id


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


@contextmanager
def _process_lock(lock_path: Path, lock_timeout_seconds: int):
    """Serialize writers across Curator instances and host processes."""
    if common.fcntl is None:
        raise KnowledgeCurationError(
            "cross-process file locking is unavailable; apply refused"
        )
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    deadline = monotonic() + lock_timeout_seconds
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


def _validator_path(workspace: Path, validator_id: str) -> Path | None:
    path = workspace / validator_id
    if path.is_symlink() or not path.is_file():
        return None
    try:
        path.resolve().relative_to(workspace)
    except ValueError:
        return None
    return path


def _run_validator(
    workspace: Path, validator_id: str, *, validator_timeout_seconds: int,
) -> KnowledgeValidatorResult:
    code = None
    if _validator_path(workspace, validator_id) is None:
        status, output = "missing", "validator is missing or not a contained regular file"
    else:
        try:
            completed = subprocess.run(
                [sys.executable, validator_id], cwd=workspace,
                text=True, encoding="utf-8", errors="replace", capture_output=True,
                timeout=validator_timeout_seconds, check=False,
            )
        except subprocess.TimeoutExpired:
            status, output = "timeout", "validator timed out"
        except OSError as exc:
            status, output = "error", f"validator could not run ({type(exc).__name__})"
        else:
            code = completed.returncode
            status = "passed" if code == 0 else "failed"
            output = (completed.stdout + completed.stderr).strip().replace(str(workspace), "<workspace>")[-4000:]
    return KnowledgeValidatorResult(
        validator_id=validator_id, passed=status == "passed", status=status,
        returncode=code, output=output,
    )


def _result(validation, updated_on, *, document_ids=(), validators=(), applied=0, rolled_back=False):
    """Project the same accepted/rejected identities for every transaction exit."""
    return KnowledgeApplyResult(
        batch_id=validation.batch_id, success=not any(not item.passed for item in validators),
        attempted=len(validation.accepted) + len(validation.rejected), applied=applied,
        accepted_indexes=tuple(item.input_index for item in validation.accepted),
        rejected_indexes=tuple(item.index for item in validation.rejected),
        updated_document_ids=document_ids, updated_on=updated_on,
        validators=tuple(validators), rolled_back=rolled_back,
    )


def _failure(result) -> KnowledgeValidatorError:
    failed = result.validators[-1]
    return KnowledgeValidatorError(
        f"knowledge validator failed: {failed.validator_id} ({failed.status})",
        result,
    )


def apply_proposals(
    workspace: Path, validation: KnowledgeProposalValidation, *,
    max_catalog_pages: int, validator_timeout_seconds: int, lock_timeout_seconds: int,
    apply_lock, lock_path: Path, updated_on: str | date | None = None,
) -> KnowledgeApplyResult:
    """Append accepted sections, gate with both validators, rollback on fail."""
    applied_on = _normalize_date(updated_on)
    proposals = validation.accepted
    if not proposals:
        return _result(validation, applied_on)

    grouped: dict[str, list[KnowledgeRuleProposal]] = defaultdict(list)
    allowed_catalog = set(catalog(workspace, validation.repository, max_catalog_pages=max_catalog_pages))
    seen_indexes: set[int] = set()
    for proposal in proposals:
        if (
            proposal.input_index < 0
            or proposal.input_index in seen_indexes
            or proposal.page_document_id not in allowed_catalog
            or section_error(proposal.rule_id, proposal.section_markdown, proposal.sources)
            or _repeated_section_rule_id(proposal.section_markdown)
            or proposal.proposal_id != _proposal_id(validation, proposal)
        ):
            raise KnowledgeCurationError(
                "accepted proposal failed apply-time integrity validation"
            )
        seen_indexes.add(proposal.input_index)
        grouped[proposal.page_document_id].append(proposal)
    document_ids = tuple(sorted(grouped))

    with apply_lock, _process_lock(lock_path, lock_timeout_seconds):
        # Validation ran without the lock: a batch validated alongside
        # this one may have landed the same new ID on ANOTHER page
        # since, which the target-page hash below cannot notice.
        # Re-check tree-wide under the lock, before any write; a
        # change to the target page itself is the hash check's job.
        existing_ids = existing_rule_ids(workspace, max_catalog_pages=max_catalog_pages)
        introduced: set[str] = set()
        for proposal in proposals:
            ids = _section_rule_ids(proposal.section_markdown)
            occupied = {rule_id: existing_ids[rule_id] for rule_id in ids
                        if rule_id in existing_ids and existing_ids[rule_id] != proposal.page_document_id}
            taken = first_taken_rule_id(ids, occupied, introduced)
            if taken:
                owner = occupied.get(taken)
                if owner is not None:
                    raise KnowledgeCurationError(f"rule_id {taken} already exists on {owner}; revalidate the batch against the current tree")
                raise KnowledgeCurationError(f"proposal is no longer append-safe: {proposal.page_document_id}")
            introduced.update(ids)


        snapshots: dict[str, bytes] = {}
        rendered: dict[str, bytes] = {}

        for document_id in document_ids:
            path = document_path(workspace, document_id)
            original = path.read_bytes()
            proposals_for_page = grouped[document_id]
            expected_hashes = {
                proposal.page_sha256 for proposal in proposals_for_page
            }
            if expected_hashes != {_sha256(original)}:
                raise KnowledgeCurationError(
                    f"target page changed after validation: {document_id}"
                )
            if any(first_taken_rule_id(_section_rule_ids(proposal.section_markdown), existing_ids)
                   for proposal in proposals_for_page):
                raise KnowledgeCurationError(f"proposal is no longer append-safe: {document_id}")
            snapshots[document_id] = original
            rendered[document_id] = _updated_page(
                original.decode("utf-8"),
                [proposal.section_markdown for proposal in proposals_for_page],
                applied_on,
            ).encode("utf-8")

        missing_results = tuple(
            result
            for validator_id in _VALIDATOR_IDS
            if not (result := _run_validator_preflight(workspace, validator_id)).passed
        )
        if missing_results:
            raise _failure(_result(validation, applied_on, document_ids=document_ids, validators=missing_results))

        try:
            for document_id in document_ids:
                _atomic_write(
                    document_path(workspace, document_id), rendered[document_id]
                )
        except OSError as exc:
            for document_id, original in snapshots.items():
                _atomic_write(document_path(workspace, document_id), original)
            raise KnowledgeCurationError(
                f"could not apply knowledge batch ({type(exc).__name__}); "
                "target pages were restored"
            ) from exc

        validator_results: list[KnowledgeValidatorResult] = []
        for validator_id in _VALIDATOR_IDS:
            result = _run_validator(workspace, validator_id, validator_timeout_seconds=validator_timeout_seconds)
            validator_results.append(result)
            if not result.passed:
                for document_id, original in snapshots.items():
                    _atomic_write(document_path(workspace, document_id), original)
                raise _failure(_result(validation, applied_on, document_ids=document_ids,
                                       validators=validator_results, rolled_back=True))

        return _result(validation, applied_on, document_ids=document_ids,
                       applied=len(proposals), validators=validator_results)


def _run_validator_preflight(
    workspace: Path, validator_id: str
) -> KnowledgeValidatorResult:
    missing = _validator_path(workspace, validator_id) is None
    return KnowledgeValidatorResult(
        validator_id=validator_id, passed=not missing,
        status="missing" if missing else "ready", returncode=None,
        output="validator is missing or not a contained regular file" if missing else "",
    )
