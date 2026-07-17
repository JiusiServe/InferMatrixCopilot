"""Cross-platform, repo-scoped access to the curated Markdown knowledge base."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


class KnowledgeDocsError(ValueError):
    """A refused or invalid knowledge-base operation."""


@dataclass(frozen=True)
class KnowledgeHit:
    path: str
    line: int
    text: str
    score: int

    def as_dict(self) -> dict:
        return {"path": self.path, "line": self.line, "text": self.text}


class KnowledgeDocs:
    """Read/search only the shared general slice and one repo-specific slice."""

    def __init__(self, root: str | Path, repo_subdir: str | None = None):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise KnowledgeDocsError(f"knowledge root does not exist: {self.root}")
        scopes: list[Path] = []
        general = (self.root / "general").resolve()
        if general.is_dir():
            scopes.append(general)
        if repo_subdir:
            repo = (self.root / repo_subdir).resolve()
            try:
                repo.relative_to(self.root)
            except ValueError as exc:
                raise KnowledgeDocsError("repo_subdir escapes the knowledge root") from exc
            if repo.is_dir():
                scopes.append(repo)
        self.scopes = tuple(dict.fromkeys(scopes))

    def _in_scope(self, path: Path) -> bool:
        for scope in self.scopes:
            try:
                path.relative_to(scope)
                return True
            except ValueError:
                continue
        return False

    def _resolve_doc(self, relative_path: str) -> Path:
        raw = Path(relative_path)
        if raw.is_absolute():
            raise KnowledgeDocsError("absolute paths are not allowed")
        target = (self.root / raw).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise KnowledgeDocsError("path escapes the knowledge root") from exc
        if not self._in_scope(target):
            raise KnowledgeDocsError("path is outside the selected knowledge slices")
        if not target.exists():
            raise FileNotFoundError(relative_path)
        if not target.is_file():
            raise KnowledgeDocsError("path is not a regular file")
        if target.suffix.casefold() != ".md":
            raise KnowledgeDocsError("only Markdown documents are readable")
        return target

    def read(self, path: str, *, offset: int = 0, limit: int = 24_000) -> dict:
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise KnowledgeDocsError("offset must be a non-negative integer")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise KnowledgeDocsError("limit must be a positive integer")
        limit = min(limit, 65_536)
        target = self._resolve_doc(path)
        data = target.read_text(encoding="utf-8", errors="replace")
        end = offset + limit
        return {
            "path": target.relative_to(self.root).as_posix(),
            "content": data[offset:end],
            "next_offset": end if end < len(data) else None,
        }

    def search(self, query: str, *, limit: int = 40) -> list[dict]:
        query = str(query).strip()
        if not query:
            raise KnowledgeDocsError("query must not be empty")
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise KnowledgeDocsError("limit must be an integer")
        limit = max(1, min(limit, 100))
        folded = query.casefold()
        terms = [t.casefold() for t in re.findall(r"[\w.-]+", query, re.UNICODE)]
        hits: list[KnowledgeHit] = []
        seen_files: set[Path] = set()
        for scope in self.scopes:
            for candidate in sorted(scope.rglob("*.md")):
                target = candidate.resolve()
                if target in seen_files or not self._in_scope(target) or not target.is_file():
                    continue
                seen_files.add(target)
                rel = target.relative_to(self.root).as_posix()
                for lineno, line in enumerate(
                        target.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    line_folded = line.casefold()
                    exact = folded in line_folded
                    term_match = bool(terms) and all(t in line_folded for t in terms)
                    path_match = folded in rel.casefold()
                    if not (exact or term_match or (path_match and lineno == 1)):
                        continue
                    score = (100 if exact else 60) + (20 if line.lstrip().startswith("#") else 0)
                    if lineno <= 12:  # title/frontmatter/tags are high-signal metadata
                        score += 10
                    if path_match:
                        score += 5
                    hits.append(KnowledgeHit(rel, lineno, line[:500], score))
        hits.sort(key=lambda h: (-h.score, h.path, h.line))
        return [hit.as_dict() for hit in hits[:limit]]
