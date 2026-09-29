"""Evidence-bound proposal validation and rule identity."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any

from ..sdk.v1.models import (
    InvalidRequestError, KnowledgeEvidenceBatch, KnowledgeProposalRejection,
    KnowledgeProposalValidation, KnowledgeRuleProposal, RepositoryRef,
)
from .common import (
    _HEADING, _MAX_SECTION_CHARS, _MAX_SOURCE_CHARS, _RULE_HEADING_ID,
    _RULE_ID, _sha256,
)


class ProposalMixin:
    @staticmethod
    def _section_rule_ids(section: str) -> tuple[str, ...]:
        """The rule IDs every heading in a section carries, in order, the
        declared one first: a nested ``###`` heading is a rule heading too.
        Repeats are kept so callers can reject a section that heads one ID
        twice (``## X-2`` over ``### X-2``, or two ``### X-3``)."""
        return tuple(
            match.group("rule") for match in _RULE_HEADING_ID.finditer(section)
        )

    @classmethod
    def _repeated_section_rule_id(cls, section: str) -> str:
        """The first rule ID a section heads more than once, else ''."""
        seen: set[str] = set()
        for heading_id in cls._section_rule_ids(section):
            if heading_id in seen:
                return heading_id
            seen.add(heading_id)
        return ""

    @staticmethod
    def _rule_exists(page_text: str, rule_id: str) -> bool:

        """Whether a heading at any level already carries this rule ID."""
        return any(
            match.group("rule") == rule_id
            for match in _RULE_HEADING_ID.finditer(page_text)
        )

    def _existing_rule_ids(self) -> dict[str, str]:

        """Every rule heading ID on every catalog page (all repositories
        and the general pages), mapped to the first page that heads it.
        Direct routing resolves a rule by exact ID, so an ID is unique
        tree-wide, not per page or per repository: a proposal may not
        reuse an ID that any other page already heads."""
        existing: dict[str, str] = {}
        for entry in self.catalog_entries():
            text = self._document_path(entry.document_id).read_text(
                encoding="utf-8"
            )
            for match in _RULE_HEADING_ID.finditer(text):
                existing.setdefault(match.group("rule"), entry.document_id)
        return existing

    @staticmethod
    def _proposal_id(
        *,
        batch_id: str,
        repository: RepositoryRef,
        input_index: int,
        page: str,
        rule_id: str,
        section: str,
        sources: tuple[str, ...],
        page_sha256: str,
    ) -> str:
        identity = json.dumps({
            "batch_id": batch_id,
            "repository": repository.to_dict(),
            "input_index": input_index,
            "page": page,
            "rule_id": rule_id,
            "section_markdown": section,
            "sources": sources,
            "page_sha256": page_sha256,
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return _sha256(identity.encode("utf-8"))

    def validate_proposals(
        self,
        document: dict[str, Any],
        batch: KnowledgeEvidenceBatch,
    ) -> KnowledgeProposalValidation:
        """Project untrusted model JSON onto valid, evidence-bound proposals."""
        self._validate_batch(batch)
        if not isinstance(document, dict):
            raise InvalidRequestError("proposal output must be a JSON object")
        if set(document) != {"rules"}:
            raise InvalidRequestError(
                "proposal output must contain only the rules field"
            )
        raw_rules = document.get("rules")
        if not isinstance(raw_rules, list):
            raise InvalidRequestError("proposal output rules must be an array")

        entries = {
            entry.document_id: entry
            for entry in self.catalog_entries(batch.repository)
        }
        catalog = set(entries)
        allowed_sources = {
            event.source_reference.strip() for event in batch.events
        }
        accepted: list[KnowledgeRuleProposal] = []
        rejected: list[KnowledgeProposalRejection] = []
        seen: set[tuple[str, str]] = set()
        # IDs already heading a section on any catalog page (every
        # repository), and the page each ID accepted earlier in this batch
        # went to: an ID is unique tree-wide.
        existing_ids = self._existing_rule_ids()
        proposed_ids: dict[str, str] = {}


        # Room consumed on each page by proposals accepted earlier in this
        # same batch, so two rules routed to one nearly full page do not
        # both pass here and then fail together at the validator.
        consumed: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))
        for index, item in enumerate(raw_rules):
            reason = ""
            if index >= batch.max_rules:
                reason = "batch rule limit exceeded"
            elif not isinstance(item, dict):
                reason = "proposal must be an object"
            elif set(item) != {
                "page", "rule_id", "section_markdown", "sources"
            }:
                reason = "proposal fields do not match the v1 shape"
            else:
                raw_page = item["page"]
                raw_rule_id = item["rule_id"]
                raw_section = item["section_markdown"]
                raw_sources = item["sources"]
                if not all(isinstance(value, str) for value in (
                    raw_page, raw_rule_id, raw_section
                )):
                    reason = "proposal text fields must be strings"
                    page = rule_id = section = ""
                    sources = ()
                elif (
                    not isinstance(raw_sources, list)
                    or any(not isinstance(value, str) for value in raw_sources)
                ):
                    reason = "proposal sources must be an array of strings"
                    page = rule_id = section = ""
                    sources = ()
                else:
                    page = raw_page.strip().replace("\\", "/")
                    rule_id = raw_rule_id.strip()
                    section = raw_section.strip()
                    sources = tuple(value.strip() for value in raw_sources)
                    heading = section.splitlines()[0] if section else ""
                    heading_match = _HEADING.match(heading)
                    if not reason and page not in catalog:
                        reason = "page is outside the repository rules catalog"
                    elif not reason and not _RULE_ID.fullmatch(rule_id):
                        reason = "rule_id has an invalid shape"
                    elif not reason and (
                        heading_match is None
                        or heading_match.group("rule") != rule_id
                        or len(re.findall(r"^##\s+", section, re.MULTILINE)) != 1
                    ):
                        reason = "section must contain one matching level-two rule heading"
                    elif not reason and not 80 <= len(section) <= _MAX_SECTION_CHARS:
                        reason = "section length is outside 80..16384 characters"
                    elif not reason and (
                        not sources
                        or len(sources) > 10
                        or any(
                            not source or len(source) > _MAX_SOURCE_CHARS
                            for source in sources
                        )
                    ):
                        reason = "sources must contain 1..10 bounded references"
                    elif not reason and not set(sources).issubset(allowed_sources):
                        reason = "proposal cites evidence outside this batch"
                    elif not reason and any(source not in section for source in sources):
                        reason = "every proposal source must be cited in the section"
                    elif not reason and (page, rule_id) in seen:
                        reason = "duplicate page/rule_id in proposal output"
                    elif not reason and rule_id in proposed_ids:
                        reason = (
                            "rule_id duplicates an earlier proposal on "
                            f"{proposed_ids[rule_id]}"
                        )
                    if not reason and self._repeated_section_rule_id(section):
                        reason = (
                            "section heads rule_id "
                            f"{self._repeated_section_rule_id(section)} more "
                            "than once"
                        )
                    if not reason:
                        # Every rule heading the section introduces, not
                        # only the declared one: a nested heading carrying
                        # another page's ID would otherwise land unchecked.
                        for heading_id in self._section_rule_ids(section):

                            owner = existing_ids.get(heading_id)
                            nested = heading_id != rule_id
                            if owner is None and nested and heading_id in proposed_ids:
                                owner = proposed_ids[heading_id]
                            if owner is None:
                                continue
                            if nested:
                                reason = (
                                    f"nested rule heading {heading_id} already "
                                    f"exists on {owner}"
                                )
                            elif owner == page:
                                reason = "rule_id already exists in the target page"
                            else:
                                reason = f"rule_id already exists on {owner}"
                            break



                    if not reason:
                        used_bytes, used_lines = consumed[page]
                        # The normalization newline is paid once per page:
                        # after the first accepted section the page ends
                        # with one.
                        add_bytes, add_lines = self._appended_size(
                            section,
                            self._document_path(page).read_bytes()
                            if (used_bytes, used_lines) == (0, 0) else b"\n",
                        )
                        entry = entries[page]
                        if (
                            used_bytes + add_bytes > entry.free_bytes
                            or used_lines + add_lines > entry.free_lines
                        ):
                            reason = (
                                "page full: section needs "
                                f"{add_bytes} bytes / {add_lines} lines but "
                                f"{entry.free_bytes - used_bytes} bytes / "
                                f"{entry.free_lines - used_lines} lines remain "
                                "before the page must split"
                            )
                        else:
                            consumed[page] = (
                                used_bytes + add_bytes, used_lines + add_lines
                            )

            if reason:
                rejected.append(KnowledgeProposalRejection(index, reason))
                continue

            page_data = self._document_path(page).read_bytes()
            page_sha256 = _sha256(page_data)
            accepted.append(KnowledgeRuleProposal(
                proposal_id=self._proposal_id(
                    batch_id=batch.batch_id,
                    repository=batch.repository,
                    input_index=index,
                    page=page,
                    rule_id=rule_id,
                    section=section,
                    sources=sources,
                    page_sha256=page_sha256,
                ),
                input_index=index,
                page_document_id=page,
                rule_id=rule_id,
                section_markdown=section,
                sources=sources,
                page_sha256=page_sha256,
            ))
            seen.add((page, rule_id))
            for heading_id in self._section_rule_ids(section):
                proposed_ids.setdefault(heading_id, page)


        return KnowledgeProposalValidation(
            batch_id=batch.batch_id,
            repository=batch.repository,
            accepted=tuple(accepted),
            rejected=tuple(rejected),
        )
