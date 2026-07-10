"""Per-language rules, in one place (concision K2).

Previously three divergent copies of "what is a source file / a symbol / an
indexed access, per language" lived in `engine/steps/review._sweep_targets`,
`profiles/establish.scan_modules`, and `profiles/repo_map`. They now share this
leaf data module. An unknown language returns empty/None so every consumer
degrades honestly (file-level sweep only / empty module scan / "use grep").
"""

from __future__ import annotations

import re

# source-file suffixes per language (module scan, repo map)
_SUFFIXES: dict[str, tuple[str, ...]] = {
    "python": (".py",),
    "rust": (".rs",),
    "go": (".go",),
    "javascript": (".ts", ".js", ".tsx", ".jsx"),
}

# symbol-definition regex per language (repo map)
_SYMBOL_RE: dict[str, re.Pattern] = {
    "python": re.compile(r"^\s*(?:async\s+def|def|class)\s+\w+[^\n]*", re.M),
    "go": re.compile(r"^(?:func|type)\s+[^\n{]+", re.M),
    "rust": re.compile(r"^\s*(?:pub\s+)?(?:fn|struct|enum|trait|impl)\s+[^\n{;]+",
                       re.M),
    "javascript": re.compile(
        r"^\s*(?:export\s+)?(?:function|class|const|interface)\s+\w+[^\n]*", re.M),
}

# (indexed-access, branch) line regexes for the review sweep, per language
_SWEEP_RE: dict[str, tuple[re.Pattern, re.Pattern]] = {
    "python": (re.compile(r"\w\[\s*0\s*\]|\.pop\(0\)|next\(iter\("),
               re.compile(r"(el)?if\b|else\b")),
}


def suffixes(language: str) -> tuple[str, ...]:
    """Source-file suffixes for `language` (empty tuple if unknown — module scan
    and repo map then find no files, degrading honestly)."""
    return _SUFFIXES.get(language, ())


def symbol_re(language: str) -> re.Pattern | None:
    """Symbol-definition regex for `language`, or None if unsupported (the repo
    map treats None as "unsupported → use grep")."""
    return _SYMBOL_RE.get(language)


def sweep_re(language: str) -> tuple[re.Pattern, re.Pattern] | None:
    """The (indexed-access, branch) line-regex pair for the review sweep of
    `language`, or None if unsupported (sweep falls back to file-level only)."""
    return _SWEEP_RE.get(language)
