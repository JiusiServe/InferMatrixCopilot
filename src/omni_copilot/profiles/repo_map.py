"""On-demand repo map (design §V2.0.2 / §V2.3.4 channel 3).

Repo structure pays off as a QUERYABLE, goal-ranked view under a token
budget (Aider/RepoGraph result) — never as a static overview injected into
prompts (ETH result). Agent steps get a `repo_map` tool; nothing here ever
enters a prompt unless the agent asks.

The symbol index is regex-based per language (no tree-sitter dependency) and
cached on disk keyed by the repo's HEAD commit — a new commit rebuilds it.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .languages import suffixes as _suffixes
from .languages import symbol_re as _symbol_re

_SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "build",
              "dist", ".tox"}


def _head_commit(repo: Path) -> str:
    """Current HEAD sha of `repo`, used as the cache key so a new commit
    invalidates the index. Returns "no-git" if git fails or the repo is untracked."""
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo),
                             capture_output=True, text=True, timeout=15)
        return out.stdout.strip() or "no-git"
    except Exception:
        return "no-git"


def build_index(repo: Path, language: str, *, max_files: int = 4_000,
                max_file_bytes: int = 200_000,
                max_symbols_per_file: int = 40) -> dict[str, list[str]]:
    """Build the symbol index: map each source file (relative path) to its list
    of regex-matched symbol definitions for `language`. Skips vcs/build/hidden
    dirs and non-source suffixes, and bounds the scan by file count, per-file
    bytes, and symbols-per-file. Returns {} when the language is unsupported."""
    pattern = _symbol_re(language)
    suffixes = _suffixes(language)
    if pattern is None:
        return {}
    index: dict[str, list[str]] = {}
    count = 0
    for path in sorted(repo.rglob("*")):
        if count >= max_files:
            break
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if any(part in _SKIP_DIRS or part.startswith(".")
               for part in path.relative_to(repo).parts[:-1]):
            continue
        count += 1
        try:
            text = path.read_text(encoding="utf-8",
                                  errors="replace")[:max_file_bytes]
        except OSError:
            continue
        symbols = [m.group(0).strip()[:120]
                   for m in pattern.finditer(text)][:max_symbols_per_file]
        if symbols:
            index[str(path.relative_to(repo))] = symbols
    return index


class RepoMap:
    """Disk-cached symbol index + query-ranked rendering."""

    def __init__(self, repo: str | Path, language: str,
                 cache_dir: str | Path | None = None):
        """Bind to `repo` (of `language`); `cache_dir`, when given, persists the
        HEAD-keyed index on disk. The index is built lazily and memoized in
        `_index`."""
        self.repo = Path(repo)
        self.language = language
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._index: dict[str, list[str]] | None = None

    @property
    def supported(self) -> bool:
        """Whether a symbol regex exists for this language (else `render` yields
        the "use grep" fallback)."""
        return _symbol_re(self.language) is not None

    def index(self) -> dict[str, list[str]]:
        """Return the symbol index, memoized. When a `cache_dir` is set, load the
        `index-<HEAD>.json` cache if present; otherwise build it, then purge stale
        caches (one HEAD, one file) and write the new one. Cache read/write errors
        degrade to an in-memory build rather than failing."""
        if self._index is not None:
            return self._index
        cache_file = None
        if self.cache_dir is not None:
            cache_file = self.cache_dir / f"index-{_head_commit(self.repo)}.json"
            if cache_file.exists():
                try:
                    self._index = json.loads(cache_file.read_text(encoding="utf-8"))
                    return self._index
                except (OSError, json.JSONDecodeError):
                    pass
        self._index = build_index(self.repo, self.language)
        if cache_file is not None:
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                for stale in self.cache_dir.glob("index-*.json"):
                    stale.unlink()   # one HEAD, one cache
                cache_file.write_text(json.dumps(self._index), encoding="utf-8")
            except OSError:
                pass
        return self._index

    def render(self, query: str, *, budget_chars: int = 4_000) -> str:
        """Render a goal-ranked slice of the index for `query`, under a
        `budget_chars` cap — the queryable view the `repo_map` tool returns.
        Files are ranked by query-word hits (path match weighted 3x symbol match);
        once ranking begins the zero-score tail is cut as noise. Returns a "use
        grep" message when the index is empty or nothing matched."""
        index = self.index()
        if not index:
            return (f"(no repo map: language '{self.language}' unsupported "
                    "or no symbols found — use grep/list_dir instead)")
        words = [w for w in re.findall(r"[a-z0-9_]+", query.lower()) if len(w) > 2]

        def score(item: tuple[str, list[str]]) -> int:
            """Relevance of one (path, symbols) entry: 3 per query word found in
            the path plus 1 per word found in the symbol text."""
            path, symbols = item
            haystack_path = path.lower()
            haystack_syms = " ".join(symbols).lower()
            return sum(3 for w in words if w in haystack_path) \
                + sum(1 for w in words if w in haystack_syms)

        ranked = sorted(index.items(), key=score, reverse=True)
        out: list[str] = []
        used = 0
        for path, symbols in ranked:
            if words and score((path, symbols)) == 0:
                break   # unranked tail is noise, not context
            block = path + "\n" + "\n".join(f"  {s}" for s in symbols)
            if used + len(block) > budget_chars:
                break
            out.append(block)
            used += len(block)
        return "\n\n".join(out) or "(no files matched the query — try grep)"
