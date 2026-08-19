#!/usr/bin/env python3
"""Validate every relative link between the repo's Markdown documents.

Why this exists: the `doc/` refactor moves ~210
files. Nothing in the repo checked that a Markdown link still resolves, so a
mass rename would have buried dead links that only a reader discovers. This
runs BEFORE the moves so the baseline is known, and stays in CI afterwards.

Scope note: `knowledge/` is deliberately excluded — it has its own two
validators (`knowledge/tools/check_wiki_lint.py` checks wiki-style links with
different rules), and duplicating that here would produce two disagreeing
verdicts on the same tree.

Exit 0 when every link resolves, 1 otherwise (with each offender printed as
`file:line -> target`).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Trees whose Markdown we own and check. `knowledge/` has its own linters.
INCLUDE = ("doc", "docs", "skills", "plugins", "integrations", "eval")
EXCLUDE_PARTS = {".venv", "node_modules", "__pycache__", ".pytest_cache",
                 ".git", "_archive"}

# Directories excluded by path, not by name, each for a distinct reason:
#   eval/dataset  — generated review artifacts. They QUOTE links out of the
#                   target repo's docs; those paths are not ours and can never
#                   resolve here. Checking them produced 250+ false positives.
#   knowledge-templates — templates, not documents. Their relative links are
#                   written to resolve AFTER the file is copied into
#                   `knowledge/`, so they are correctly broken in place.
EXCLUDE_TREES = ("eval/dataset", "doc/knowledge/templates")

# `[text](target)` — but not images with an empty target, and not reference defs.
LINK = re.compile(r"\[[^\]]*\]\(\s*([^)\s]+?)\s*(?:\s+\"[^\"]*\")?\)")
SKIP_PREFIX = ("http://", "https://", "mailto:", "#", "tel:", "data:")
FENCE = re.compile(r"^\s*(```|~~~)")


def markdown_files() -> list[Path]:
    """Every Markdown file this checker owns: repo-root pages plus the
    INCLUDE trees, minus build/vendor directories."""
    found = [p for p in REPO.glob("*.md")]
    for top in INCLUDE:
        root = REPO / top
        if not root.is_dir():
            continue
        found += [p for p in root.rglob("*.md")
                  if not EXCLUDE_PARTS & set(p.parts)
                  and not _in_excluded_tree(p)]
    return sorted(found)


def _in_excluded_tree(path: Path) -> bool:
    """Whether a file sits under one of the EXCLUDE_TREES paths."""
    rel = path.relative_to(REPO).as_posix()
    return any(rel.startswith(tree + "/") for tree in EXCLUDE_TREES)


def broken_links(path: Path) -> list[tuple[int, str]]:
    """Every unresolvable relative link in one file, as (line_no, target).

    A link is resolved against the file's own directory, matching how GitHub
    and every Markdown viewer render it. Fragments and query strings are
    stripped before the existence test: `guide.md#section` is a link to
    `guide.md`, and a missing *anchor* is not something this tool claims to
    detect.

    Two classes are skipped as illustrative rather than real: anything inside a
    fenced code block (docs show example trees and commands there, and those
    paths are not links the reader clicks) and any target containing angle
    brackets (`<page>.md` is a placeholder in a template).
    """
    bad: list[tuple[int, str]] = []
    in_fence = False
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for target in LINK.findall(line):
            if target.startswith(SKIP_PREFIX) or "<" in target or ">" in target:
                continue
            clean = target.split("#", 1)[0].split("?", 1)[0]
            if not clean:  # pure anchor, e.g. [x](#section)
                continue
            resolved = (path.parent / clean).resolve()
            if not resolved.exists():
                bad.append((lineno, target))
    return bad


def main() -> int:
    """Check every owned Markdown file; print offenders and return an exit code."""
    failures = 0
    for path in markdown_files():
        rel = path.relative_to(REPO)
        for lineno, target in broken_links(path):
            print(f"{rel}:{lineno} -> {target}")
            failures += 1
    if failures:
        print(f"\ncheck_doc_links: {failures} broken link(s)")
        return 1
    print(f"check_doc_links: OK ({len(markdown_files())} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
