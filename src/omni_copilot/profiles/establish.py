"""Profile establishment helpers (doc/DESIGN.md §V2.3.3, Stages 0–1.5).

The redundancy filter is the ETH-study lesson (§V2.0.1): context that
duplicates what the repo's own docs already say is pure cost — agents read
those docs anyway. Only the non-obvious residue may enter the briefing.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

# human-authored agent instruction files: highest-trust briefing input,
# ingested rather than re-derived
HUMAN_DOC_NAMES = ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md")

_WORD = re.compile(r"[a-z0-9`_./\-]+")
_SHINGLE = 6


def _words(text: str) -> list[str]:
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
