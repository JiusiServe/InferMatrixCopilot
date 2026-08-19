#!/usr/bin/env python3
"""Assert that every `doc/...` path cited from code actually exists.

Why this exists, measured: 29 places in `src/`, `test/` and `skills/` cite a
`doc/` page from a docstring or comment — 17 of them point at a single file
(`RFC-provider-registry.md`), which the refactor renames and moves into
`doc/features/`. These are prose references inside code: no import resolves
them, no test touches them, and no linter looked at them. Renaming a doc would
silently leave a docstring pointing at nothing.

This is the safety net for the refactor's P1 (pure migration) and stays in CI
so future doc moves cannot break in-code citations either.

Exit 0 when every cited path exists, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Trees that may cite docs. `doc/` and `docs/` themselves are handled by
# check_doc_links.py (relative-link semantics differ from these repo-root paths).
SEARCH = ("src", "test", "skills", "playbooks", "adapters", "integrations",
          "tools", "scripts", ".github")
SUFFIXES = (".py", ".md", ".yaml", ".yml", ".toml", ".json", ".sh", ".cmd", ".ps1")
EXCLUDE_PARTS = {".venv", "__pycache__", ".pytest_cache", ".git"}

# A repo-root-relative doc path under `doc/` (singular), ending in a real
# extension. Trailing punctuation is excluded from the match so
# a trailing sentence period does not become part of the filename.
#
# Deliberately NOT `docs?/`: plural `docs/` is ambiguous — it is the TARGET
# repo's documentation tree, which knowledge pages, adapters and MCP tests
# legitimately reference by upstream path (`docs/design/module/index.md`), and
# which `test/` also fabricates as tmp_path fixtures. Matching it produced only
# false positives. This repo's own `docs/` directory was dissolved by the doc
# refactor, after which `doc/` is the sole owned prefix.
CITATION = re.compile(r"\b(doc/[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:md|toml|json|yaml|yml|tsv|txt|py))")

# Paths built from pathlib SEGMENTS rather than written as one string:
#     (ROOT / "docs" / "codex" / "README.md").read_text()   # doc-citation-exempt
# The string scan above cannot see these, and exactly one such reference
# (test/test_imcifix_skill.py) survived the refactor's path sweep and broke a
# test. Reconstruct the path from the quoted segments and check it too.
SEGMENTS = re.compile(
    r"""(?:ROOT|REPO|REPO_ROOT)\s*/\s*("docs?")((?:\s*/\s*"[^"]+")+)""")
SEGMENT_PART = re.compile(r'"([^"]+)"')

# Opt-out for lines that legitimately name a path which may not exist: an
# illustrative example in a comment, or a deliberate fallback candidate (this
# tool's siblings accept both the pre- and post-migration SPEC location). An
# explicit per-line marker beats excluding whole directories, which would let a
# real dangling citation hide inside an exempted tree.
EXEMPT = "doc-citation-exempt"


def source_files() -> list[Path]:
    """Every file in the SEARCH trees that could carry a doc citation."""
    found: list[Path] = []
    for top in SEARCH:
        root = REPO / top
        if not root.is_dir():
            continue
        found += [p for p in root.rglob("*")
                  if p.is_file() and p.suffix in SUFFIXES
                  and not EXCLUDE_PARTS & set(p.parts)]
    return sorted(found)


def main() -> int:
    """Scan for cited doc paths, report the ones that do not exist."""
    missing: list[tuple[Path, int, str]] = []
    checked = 0
    for path in source_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if EXEMPT in line:
                continue
            for citation in CITATION.findall(line):
                checked += 1
                if not (REPO / citation).exists():
                    missing.append((path.relative_to(REPO), lineno, citation))
            for head, tail in SEGMENTS.findall(line):
                joined = "/".join([head.strip('"')] + SEGMENT_PART.findall(tail))
                checked += 1
                if not (REPO / joined).exists():
                    missing.append((path.relative_to(REPO), lineno,
                                    f"{joined} (built from path segments)"))
    for rel, lineno, citation in missing:
        print(f"{rel}:{lineno} cites missing {citation}")
    if missing:
        print(f"\ncheck_doc_citations: {len(missing)} dangling citation(s) "
              f"of {checked} checked")
        return 1
    print(f"check_doc_citations: OK ({checked} citations resolve)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
