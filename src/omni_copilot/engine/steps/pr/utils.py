"""Pure helper for the PR-debug steps: root-cause signature extraction from a
CI log. No state, no I/O — kept apart from the step handlers (and re-exported
from the package) so `debug.group_failures` and the tests share one source.
"""

from __future__ import annotations

import re

_ERROR_LINE = re.compile(
    r"^(E\s{3}.*|.*(?:Error|Exception|FAILED|fatal error)[:\s].*|AssertionError.*)$",
    re.MULTILINE,
)


def extract_signature(log: str) -> str:
    """Prefer the deepest root-cause-looking line over surface symptoms."""
    matches = [m.group(0).strip() for m in _ERROR_LINE.finditer(log)]
    for line in reversed(matches):  # deepest first
        if not re.search(r"(APIConnectionError|EngineDeadError|ConnectionRefused)", line):
            return line[:200]
    return (matches[-1][:200] if matches else log.strip().splitlines()[-1][:200]
            if log.strip() else "unknown failure")
