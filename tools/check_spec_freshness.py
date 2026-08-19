#!/usr/bin/env python3
"""Detect SPEC pages that fell behind the source they constrain.

Why this exists, measured on 2026-08-17: of 42 SPEC content pages, **41 were
older than their own source file and exactly 1 was in sync**, and ~17 modules
had no page at all — including all of `providers/` and the whole MCP surface.
Rewriting those pages once fixes the symptom; this tool fixes the process, by
making "source moved, spec did not" a check instead of a discovery.

Three independent failure modes are reported:

- **stale** — the source changed after the page was last verified. The page may
  still be correct (a source commit can be a typo fix), so this is a prompt to
  re-verify, and `--strict` decides whether it fails the build.
- **undeclared** — the page carries no `verified-against:` marker, so its
  freshness can only be guessed from git dates. See VERIFIED below for why that
  guess is not trustworthy after a rename.
- **uncovered** — a source module no SPEC page maps to. This one is
  unambiguous: nothing documents what must not break in that file.

Mapping: `SPEC/<rel>.md` covers `src/infermatrix_copilot/<rel>.py`, or the
package directory `<rel>/` when one exists (so `SPEC/engine/steps/pr.md`
covers every file under `engine/steps/pr/`). Pages whose names start with `_`
plus `README.md` are cross-cutting and map to no single source.

Exit 0 when clean; 1 when anything is uncovered, or when `--strict` and
anything is stale.
"""

from __future__ import annotations

import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PKG = REPO / "src" / "infermatrix_copilot"

# The refactor moves SPEC under architecture/; accept both so this tool works
# before, during and after the migration.
# Both the current and the pre-refactor location, so this tool works before,
# during and after the migration. doc-citation-exempt: naming two candidate
# paths is the point — one of them is expected not to exist.
_SPEC_REL = ("doc/architecture/SPEC", "doc/SPEC")
SPEC_CANDIDATES = tuple(REPO / p for p in _SPEC_REL)

# Pages that intentionally constrain something other than one src module.
CROSS_CUTTING_PREFIX = "_"
SPECIAL_SOURCES = {"playbooks/PLAYBOOKS": REPO / "playbooks"}


def spec_root() -> Path | None:
    """Wherever the SPEC tree currently lives, or None if absent."""
    return next((p for p in SPEC_CANDIDATES if p.is_dir()), None)


def _history_start() -> list[str]:
    """Revisions to date files from, skipping GitHub's synthetic PR merge.

    On a `pull_request` event the runner checks out `refs/pull/N/merge` — the
    branch merged into the base, a commit that exists nowhere else. A file
    edited on BOTH sides then differs from both parents, so git reports the
    merge as the commit that last touched it and the file dates to merge time.
    Its page can never be fresh however recently a human verified it, and the
    same SHA passes on the push run while failing on the pull_request run.

    The test is the event, not the shape of HEAD. "Tip is a merge" would also
    swallow a real conflict resolution pushed as the tip, which genuinely edits
    source and must keep counting. Under `pull_request` the tip is always
    GitHub's synthetic merge — a resolution of the branch's own would sit at
    HEAD^2 — so keying on the event skips exactly the commit that is not real
    history and nothing else.
    """
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        return ["HEAD"]
    out = subprocess.run(
        ["git", "rev-list", "--parents", "-n", "1", "HEAD"],
        cwd=REPO, capture_output=True, text=True).stdout.split()
    parents = out[1:]
    return parents if len(parents) > 1 else ["HEAD"]


def last_commit(path: Path) -> int:
    """Unix timestamp of the newest commit touching `path`, or 0 when untracked.

    0 means "not in history yet", which the callers treat as fresh: a brand-new
    page cannot be behind anything, and flagging it would make every commit
    that adds a spec fail its own check.
    """
    out = subprocess.run(
        ["git", "log", "-1", "--format=%ct", *_history_start(), "--", str(path)],
        cwd=REPO, capture_output=True, text=True).stdout.strip()
    return int(out) if out.isdigit() else 0


# A page may DECLARE the source revision it was checked against:
#     <!-- verified-against: 2026-08-17 -->
# This is the authoritative signal and the reason it exists: git dates cannot
# carry it. Moving a page (as the doc refactor does for all 45 of them)
# rewrites its last-commit date to the move, which would make every July-era
# page look permanently current — the migration would silently defeat this
# check. A declared date survives moves, reformats, and typo fixes, and it
# states a fact a commit date only implies: a human compared page to source.
VERIFIED = re.compile(r"verified-against:\s*(\d{4}-\d{2}-\d{2})")


def verified_date(path: Path) -> int:
    """The page's declared verification date as a timestamp, or 0 if undeclared.

    Only the head of the file is scanned: this marker belongs next to the title,
    and accepting it anywhere would let a stale page be "refreshed" by a line
    buried at the bottom.
    """
    head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:15])
    match = VERIFIED.search(head)
    if not match:
        return 0
    return int(datetime.datetime.strptime(match.group(1), "%Y-%m-%d").timestamp())


def source_for(rel: str) -> Path | None:
    """The source file or package directory a SPEC page constrains."""
    if rel in SPECIAL_SOURCES:
        found = SPECIAL_SOURCES[rel]
        return found if found.exists() else None
    module = PKG / f"{rel}.py"
    if module.is_file():
        return module
    package = PKG / rel
    return package if package.is_dir() else None


def spec_pages(root: Path) -> list[tuple[str, Path]]:
    """Every content page as (rel-without-suffix, path); cross-cutting excluded."""
    pages = []
    for path in sorted(root.rglob("*.md")):
        # The `_` convention marks cross-cutting pages, but ONLY at the SPEC
        # root (_ARCHITECTURE / _CONCISION / _CONSTRAINTS). Nested underscore
        # names are ordinary module pages — `engine/steps/_common.md` documents
        # `engine/steps/_common.py` — and skipping those reported a real,
        # covered module as uncovered.
        # Cross-cutting pages use a SINGLE leading underscore (_ARCHITECTURE,
        # _CONSTRAINTS, _CONCISION). A dunder name is an ordinary module page —
        # `__main__.md` documents `__main__.py` — so the prefix test must not
        # swallow it, or a covered module reads as uncovered.
        at_root = path.parent == root
        cross_cutting = (path.name.startswith(CROSS_CUTTING_PREFIX)
                         and not path.name.startswith("__"))
        if path.name == "README.md" or (at_root and cross_cutting):
            continue
        pages.append((str(path.relative_to(root).with_suffix("")).replace("\\", "/"),
                      path))
    return pages


def source_modules() -> list[str]:
    """Every src module that needs coverage, as a rel path without suffix.

    `__init__.py` files are excluded: they are re-export shims whose contract is
    the package's, and requiring a page per package `__init__` would inflate the
    tree without documenting a single additional invariant.
    """
    return sorted(
        str(p.relative_to(PKG).with_suffix("")).replace("\\", "/")
        for p in PKG.rglob("*.py")
        if p.name != "__init__.py" and "__pycache__" not in p.parts)


def main() -> int:
    """Report stale and uncovered SPEC coverage; return an exit code."""
    strict = "--strict" in sys.argv
    root = spec_root()
    if root is None:
        print("check_spec_freshness: no SPEC tree found — nothing to check")
        return 0

    pages = spec_pages(root)
    covered_by = {rel for rel, _ in pages}

    stale: list[tuple[str, str, str]] = []
    undeclared: list[str] = []
    orphan: list[str] = []
    for rel, path in pages:
        src = source_for(rel)
        if src is None:
            orphan.append(rel)
            continue
        src_t = last_commit(src)
        declared = verified_date(path)
        if declared:
            # Compare by DAY, not timestamp. The marker has date granularity,
            # so it parses to midnight; a commit made later the same day would
            # otherwise read as "source newer than the verification" and every
            # page would be born stale on the day it was written.
            if _day(src_t) > _day(declared):
                stale.append((rel, _day(declared), _day(src_t)))
            continue
        # No marker: fall back to git dates, and say so. The fallback is only a
        # hint — a rename resets it — which is exactly why the marker exists.
        undeclared.append(rel)
        spec_t = last_commit(path)
        if spec_t and src_t > spec_t:
            stale.append((rel, _day(spec_t) + "*", _day(src_t)))

    uncovered = [m for m in source_modules()
                 if not any(m == c or m.startswith(c + "/") for c in covered_by)]

    if stale:
        print(f"STALE — source changed after the spec was verified ({len(stale)}):")
        for rel, sd, cd in stale:
            print(f"  {rel:38s} verified {sd:12s} code {cd}")
        print("  (* = inferred from git dates, no verified-against: marker)")
    if undeclared:
        print(f"\nUNDECLARED — no `verified-against:` marker ({len(undeclared)}):")
        for rel in undeclared:
            print(f"  {rel}")
    if uncovered:
        print(f"\nUNCOVERED — no SPEC page maps to these ({len(uncovered)}):")
        for m in uncovered:
            print(f"  {m}")
    if orphan:
        print(f"\nORPHAN — spec page with no matching source ({len(orphan)}):")
        for rel in orphan:
            print(f"  {rel}")

    total = len(pages)
    verified = total - len(undeclared) - len(orphan)
    print(f"\ncheck_spec_freshness: {total} pages — {verified} declared-verified, "
          f"{len(stale)} stale, {len(undeclared)} undeclared, {len(orphan)} orphan; "
          f"{len(uncovered)} modules uncovered")
    if uncovered or orphan:
        return 1
    return 1 if (strict and (stale or undeclared)) else 0


def _day(ts: int) -> str:
    """A commit timestamp as YYYY-MM-DD, for a readable report."""
    import datetime
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


if __name__ == "__main__":
    sys.exit(main())
