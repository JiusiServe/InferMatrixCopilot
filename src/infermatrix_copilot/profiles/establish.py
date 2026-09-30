"""Profile establishment helpers (doc/architecture/DESIGN.md §V2.3.3, Stages 0–1.5).

The redundancy filter is the ETH-study lesson (§V2.0.1): context that
duplicates what the repo's own docs already say is pure cost — agents read
those docs anyway. Only the non-obvious residue may enter the briefing.
"""

from __future__ import annotations

import fnmatch
import hashlib
import re
from pathlib import Path, PurePosixPath
from typing import Sequence

# human-authored agent instruction files: highest-trust briefing input,
# ingested rather than re-derived
HUMAN_DOC_NAMES = ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md")

_WORD = re.compile(r"[a-z0-9`_./\-]+")
_SHINGLE = 6


def _words(text: str) -> list[str]:
    """Lowercased word tokens of `text` (identifier/path chars kept) — the shared
    normalization for both the doc corpus and the redundancy shingling."""
    return _WORD.findall(text.lower())


def fact_id(prefix: str, text: str) -> str:
    """Deterministic id from the text — re-runs confirm instead of duplicate."""
    return f"{prefix}-{hashlib.sha1(text.encode()).hexdigest()[:8]}"


def build_doc_corpus(repo: Path, *, max_files: int = 50,
                     max_chars: int = 400_000) -> str:
    """Normalized text of the repo's own documentation (README* + docs/)."""
    texts: list[str] = []
    total = 0
    candidates = sorted(repo.glob("README*")) + sorted((repo / "docs").rglob("*.md")
                                                       if (repo / "docs").exists()
                                                       else [])
    for path in candidates[:max_files]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        texts.append(" ".join(_words(text)))
        total += len(text)
        if total > max_chars:
            break
    return " ".join(texts)


def is_redundant(text: str, corpus: str) -> bool:
    """True when the fact substantially restates the docs: any 6-word shingle
    of the fact appears verbatim in the corpus (whole phrase for short facts)."""
    if not corpus:
        return False
    words = _words(text)
    if not words:
        return True
    if len(words) < _SHINGLE:
        return " ".join(words) in corpus
    return any(" ".join(words[i:i + _SHINGLE]) in corpus
               for i in range(len(words) - _SHINGLE + 1))


def extract_directives(doc_text: str, *, min_words: int = 4,
                       max_words: int = 60) -> list[str]:
    """Bullet lines of a human instruction file — short imperative directives
    are the content class the ETH study found effective."""
    out: list[str] = []
    for line in doc_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith(("- ", "* ")):
            continue
        text = stripped[2:].strip().rstrip(".")
        if min_words <= len(text.split()) <= max_words:
            out.append(text)
    return out


_NON_MODULE_DIRS = {"docs", "doc", "examples", "example", "scripts", "assets",
                    "third_party", "vendor"}


def scan_modules(repo: Path, language: str, *, min_files: int = 3) -> dict:
    """Deterministic module draft: top-level directories holding enough source
    files. Tests keep their own module so wave scheduling can order them."""
    from .languages import suffixes as _suffixes
    sfx = _suffixes(language)
    modules: dict[str, dict] = {}
    for entry in sorted(repo.iterdir()):
        if (not entry.is_dir() or entry.name.startswith(".")
                or entry.name in _NON_MODULE_DIRS):
            continue
        count = sum(1 for p in entry.rglob("*")
                    if p.is_file() and p.suffix in sfx)
        if count >= min_files:
            wave = 2 if entry.name in ("tests", "test", "benchmarks") else 1
            modules[entry.name] = {"local_paths": [f"{entry.name}/"],
                                   "wave": wave}
    return modules


ROOT_MODULE = "./"  # the key of the module holding files directly in the repo root


def _loc(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return sum(1 for line in text.splitlines() if line.strip())


def normalize_root(root: str) -> str:
    """A source root as a repo-relative POSIX directory without leading ``./``
    or slashes (``"src/pkg"``); the repository root itself is ``""``."""
    text = PurePosixPath(root.strip().strip("/") or ".").as_posix()
    return "" if text == "." else text


def _module_parent(key: str) -> str:
    parent = str(PurePosixPath(key.rstrip("/")).parent)
    return ROOT_MODULE if parent == "." else parent + "/"


def scan_modules_at_depth(repo: Path, language: str, *, source_roots: Sequence[str],
                          depth: int, min_loc: int,
                          exclude: Sequence[str] = ()) -> dict[str, dict]:
    """Deterministic directory-level modules for knowledge coverage.

    Every source file under a source root belongs to the module of its deepest
    ancestor directory at most ``depth`` levels below that root (the root is
    level 0). A module under ``min_loc`` non-blank lines folds into its parent
    directory's module, deepest first and until stable; a source root never
    folds. Returns ``{"pkg/sub/": {"files": [...], "loc": n}}`` (files directly
    in the repo root: ``ROOT_MODULE``). Hidden and non-code directories are
    skipped at every level, ``exclude`` fnmatch globs apply to repo-relative
    file paths, and an unknown language scans nothing rather than guessing."""
    from .languages import suffixes as _suffixes

    sfx = _suffixes(language)
    if not sfx or depth < 0:
        return {}
    roots = sorted({normalize_root(r) for r in source_roots}) or [""]
    if "" in roots:
        roots = [""]  # the repository root already holds every other root
    modules: dict[str, dict] = {}
    seen: set[str] = set()
    root_keys: set[str] = set()
    # longest root first, so a nested root owns its own files
    for root in sorted(roots, key=lambda r: (-len(r), r)):
        base = repo / root if root else repo
        if not base.is_dir():
            continue
        root_key = f"{root}/" if root else ROOT_MODULE
        root_keys.add(root_key)
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in sfx:
                continue
            rel = path.relative_to(repo).as_posix()
            if rel in seen or any(fnmatch.fnmatch(rel, glob) for glob in exclude):
                continue
            parts = path.relative_to(base).parts[:-1]
            if any(p.startswith(".") or p in _NON_MODULE_DIRS for p in parts):
                continue
            seen.add(rel)
            key = (f"{root}/" if root else "") + "".join(f"{p}/" for p in parts[:depth])
            entry = modules.setdefault(key or ROOT_MODULE, {"files": [], "loc": 0})
            entry["files"].append(rel)
            entry["loc"] += _loc(path)
    folding = True
    while folding:  # one fold per pass, deepest first: a folded child counts toward its parent
        folding = False
        for key in sorted(modules, key=lambda k: (-k.count("/"), k)):
            parent = _module_parent(key)
            if key in root_keys or parent == key or modules[key]["loc"] >= min_loc:
                continue
            entry = modules.pop(key)
            target = modules.setdefault(parent, {"files": [], "loc": 0})
            target["files"].extend(entry["files"])
            target["loc"] += entry["loc"]
            folding = True
            break
    return {key: {"files": sorted(entry["files"]), "loc": entry["loc"]}
            for key, entry in sorted(modules.items()) if entry["files"]}
