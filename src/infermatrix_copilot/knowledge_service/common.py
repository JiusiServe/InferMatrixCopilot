"""Shared rule syntax, bounds, hashing, errors, and lock capability."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Final

from ..sdk.v1.models import (
    KnowledgeApplyResult,
    KnowledgeCurationError,
)

_RULE_ID: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{1,40}")
_HEADING: Final = re.compile(r"^##\s+(?P<rule>[A-Za-z0-9][A-Za-z0-9-]{1,40})\s+[—-]\s+\S")
# Any rule heading on a page, by ID, at any heading level (owner pages
# nest some rules under ``###``): the tree-wide uniqueness scan.
_RULE_HEADING_ID: Final = re.compile(
    r"^#{2,6}\s+(?P<rule>[A-Za-z0-9][A-Za-z0-9-]{1,40})(?=\s|$)", re.MULTILINE
)


_FRONTMATTER: Final = re.compile(
    r"\A---(?P<open>\r?\n)(?P<body>.*?)(?P<close>\r?\n)---(?P<after>\r?\n|\Z)",
    re.DOTALL,
)
_UPDATED: Final = re.compile(r"^updated:[^\r\n]*$", re.MULTILINE)
_VALIDATOR_IDS: Final = (
    "knowledge/tools/check_knowledge_tree.py",
    "knowledge/tools/check_wiki_lint.py",
)
# Owner rule pages: the entry page plus its split-out topic pages, which the
# tree already treats as rule pages (frontmatter ``type: rule``).
_RULE_PAGE_NAME: Final = re.compile(r"rules(?:-[a-z0-9][a-z0-9-]*)?\.md")
_PAGE_TYPE: Final = re.compile(r"^type:\s*(?P<type>[A-Za-z]+)\s*$", re.MULTILINE)
# Mirrors knowledge/tools/check_knowledge_tree.py's split gate: a page fails
# at >= 32 KiB or >= 500 non-empty lines, so that is the capacity a proposal
# may consume before validation would reject the whole batch.
_PAGE_MAX_BYTES: Final = 32 * 1024
_PAGE_MAX_LINES: Final = 500
_MAX_SECTION_CHARS = 16 * 1024
_MAX_SUMMARY_CHARS = 3000
# Diff evidence: enough of a change to see the contract it fixed or added,
# bounded in UTF-8 bytes (markers included) so twenty events still fit one
# model call whatever script the diff is written in.
_MAX_DIFF_BYTES = 8 * 1024
_MAX_BATCH_DIFF_BYTES = 160 * 1024
_DIFF_TRUNCATED = "\n[diff excerpt truncated by the SDK at its per-event bound]"
_DIFF_BUDGET_EXHAUSTED = "[diff excerpt omitted: the batch diff budget is exhausted]"
_MAX_ATTRIBUTE_CHARS = 3000
_MAX_CHANGED_PATHS = 50
_MAX_SOURCE_CHARS = 60

try:
    import fcntl
except ImportError:  # pragma: no cover - exercised on platforms without flock
    fcntl = None  # type: ignore[assignment]


class KnowledgeValidatorError(KnowledgeCurationError):
    """The fixed validator gate failed and all target pages were restored."""

    code = "knowledge_validator_failed"

    def __init__(self, message: str, result: KnowledgeApplyResult):
        super().__init__(message)
        self.result = result


def _apply_supported() -> bool:
    """Whether this platform can provide the apply transaction's lock."""
    return fcntl is not None


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _json_for_prompt(value: object) -> str:
    """Serialize untrusted data without allowing it to close the data fence."""
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    return encoded.replace("<", r"\u003c").replace(">", r"\u003e")
