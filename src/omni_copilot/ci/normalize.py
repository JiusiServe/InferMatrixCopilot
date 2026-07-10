"""Failure-signature normalization (design §V2.1(c)).

Grouping and known-flaky matching must compare the FAILURE, not the noise
around it: timestamps, hashes, addresses, temp paths, line numbers and
durations vary run to run, so exact-string comparison misclassifies repeats
as new failures (the parent monitor's known weakness — deliberately not
inherited here). Small literal numbers are kept: `assert 1 == 2` is signal.
"""

from __future__ import annotations

import re

_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"0x[0-9a-fA-F]+"), "<addr>"),
    (re.compile(r"\b[0-9a-f]{7,40}\b"), "<hash>"),
    (re.compile(r"\d{4}-\d{2}-\d{2}[T ]?(\d{2}:\d{2}(:\d{2})?(\.\d+)?Z?)?"), "<ts>"),
    (re.compile(r"\b\d{2}:\d{2}:\d{2}(\.\d+)?\b"), "<time>"),
    (re.compile(r"(/tmp|/var/folders|/home/[^/\s]+|/root)/\S*"), "<path>"),
    (re.compile(r"\bline \d+\b"), "line <n>"),
    (re.compile(r"(?<=:)\d+(?=[\s:,)\]]|$)"), "<n>"),   # file.py:123
    (re.compile(r"\b\d+(\.\d+)?\s*(s|ms|sec|seconds)\b"), "<dur>"),
    (re.compile(r"\b\d{5,}\b"), "<n>"),                  # big ids/ports/pids
]


def normalize_signature(signature: str) -> str:
    out = signature
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    return re.sub(r"\s+", " ", out).strip()
