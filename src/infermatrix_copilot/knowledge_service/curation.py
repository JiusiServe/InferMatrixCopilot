"""Provider-owned knowledge curation behind the SDK v1 facade."""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path
from tempfile import gettempdir
from typing import Any

from ..sdk.v1.models import InvalidRequestError, KnowledgeCurationError
from .apply import ApplyMixin
from .catalog import CatalogMixin
from .common import KnowledgeValidatorError, _RULE_ID, _apply_supported
from .prompt import PromptMixin
from .proposals import ProposalMixin


__all__ = ["KnowledgeCurator", "KnowledgeValidatorError", "_apply_supported"]


class KnowledgeCurator(ApplyMixin, ProposalMixin, PromptMixin, CatalogMixin):
    @staticmethod
    def reviewed_rule_evidence(page_text: str, *, rule_id: str, source_reference: str) -> dict[str, str]:
        """Verify one active, source-citing rule and return its exact block digest."""
        from .lifecycle import Page

        sections = [section for section in Page.parse(page_text).rules() if section.rule_id == rule_id]
        if len(sections) != 1 or sections[0].footer.status != "active" or source_reference not in sections[0].citations:
            raise KnowledgeCurationError("reviewed rule must exist once, be active, and cite its source")
        return {"rule_id": rule_id, "source_reference": source_reference,
                "section_sha256": hashlib.sha256(sections[0].text.encode("utf-8")).hexdigest()}

    @staticmethod
    def installed_knowledge_file(path: str) -> bytes:
        """Read a canonical governed page from this installed provider package."""
        from importlib.resources import files

        from .lifecycle import safe_source_path

        if not safe_source_path(path) or not path.startswith("knowledge/repos/") or not path.endswith(".md"):
            raise InvalidRequestError("installed knowledge path must be a canonical repository Markdown page")
        target = files("infermatrix_copilot").joinpath(*path.split("/"))
        try:
            return target.read_bytes()
        except (OSError, ValueError) as exc:
            raise KnowledgeCurationError("installed provider knowledge page is unavailable") from exc

    def __init__(
        self,
        workspace_root: str | Path,
        *,
        max_rules: int = 8,
        max_events: int = 20,
        max_catalog_pages: int = 200,
        validator_timeout_seconds: int = 600,
        lock_timeout_seconds: int = 30,
    ) -> None:
        if not 1 <= max_rules <= 32:
            raise InvalidRequestError("max_rules must be within 1..32")
        if not 1 <= max_events <= 100:
            raise InvalidRequestError("max_events must be within 1..100")
        if not 1 <= max_catalog_pages <= 2000:
            raise InvalidRequestError("max_catalog_pages must be within 1..2000")
        if validator_timeout_seconds < 1:
            raise InvalidRequestError("validator_timeout_seconds must be >= 1")
        if not 1 <= lock_timeout_seconds <= 300:
            raise InvalidRequestError("lock_timeout_seconds must be within 1..300")
        self._workspace = Path(workspace_root).expanduser().resolve()
        self._knowledge = self._workspace / "knowledge"
        if not (self._knowledge / "AGENTS.md").is_file():
            raise KnowledgeCurationError(
                "workspace has no governed knowledge/AGENTS.md"
            )
        self.max_rules = int(max_rules)
        self.max_events = int(max_events)
        self.max_catalog_pages = int(max_catalog_pages)
        self.validator_timeout_seconds = int(validator_timeout_seconds)
        self.lock_timeout_seconds = int(lock_timeout_seconds)
        self._apply_lock = threading.Lock()
        lock_key = hashlib.sha256(str(self._workspace).encode("utf-8")).hexdigest()
        self._lock_path = (
            Path(gettempdir())
            / "infermatrix-copilot"
            / "knowledge-curator"
            / f"{lock_key}.lock"
        )

    @staticmethod
    def proposal_schema(*, max_rules: int = 8) -> dict[str, Any]:
        """JSON Schema for the untrusted model response."""
        if not 1 <= max_rules <= 32:
            raise InvalidRequestError("max_rules must be within 1..32")
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "required": ["rules"],
            "properties": {
                "rules": {
                    "type": "array",
                    "maxItems": max_rules,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "page", "rule_id", "section_markdown", "sources"
                        ],
                        "properties": {
                            "page": {"type": "string"},
                            "rule_id": {
                                "type": "string",
                                "pattern": f"^{_RULE_ID.pattern}$",
                            },
                            "section_markdown": {"type": "string"},
                            "sources": {
                                "type": "array",
                                "minItems": 1,
                                "maxItems": 10,
                                "items": {"type": "string"},
                            },
                        },
                    },
                }
            },
        }
