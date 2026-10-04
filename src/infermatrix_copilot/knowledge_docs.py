"""Cross-platform, repo-scoped access to the curated Markdown knowledge base."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .knowledge_service.lifecycle import (
    DEPTH_FACETS, LifecycleError, Page, depth_sections, safe_source_path as _source_path, visible_text,
)


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

    def __init__(
        self,
        root: str | Path,
        repo_subdir: str | None = None,
        *,
        verify: Callable[[str], Path] | None = None,
    ):
        # `verify(rel)` is called before every file is read; an activated
        # knowledge snapshot passes `KnowledgeView.path`, which raises when a
        # file is missing from, or differs from, the snapshot manifest.
        self._verify = verify
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
        self.repo_scope = next((p for p in self.scopes if p != general), None)

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
        self._checked(target)
        return target

    def _checked(self, target: Path) -> None:
        if self._verify is not None:
            self._verify(target.relative_to(self.root).as_posix())

    def read(self, path: str, *, offset: int = 0, limit: int = 24_000) -> dict:
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise KnowledgeDocsError("offset must be a non-negative integer")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise KnowledgeDocsError("limit must be a positive integer")
        limit = min(limit, 65_536)
        target = self._resolve_doc(path)
        data = visible_text(target.read_text(encoding="utf-8", errors="replace"))
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
                self._checked(target)
                rel = target.relative_to(self.root).as_posix()
                served = visible_text(target.read_text(encoding="utf-8", errors="replace"))
                for lineno, line in enumerate(served.splitlines(), 1):
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

    def related(self, changed_files: list[str], *, query: str = "") -> dict:
        """Select at most two explanatory documents with 6k characters of prose.

        Source/entry-point matches outrank declared globs and description hints.
        Hints select context; they do not attest the PR head's behavior.
        """
        if not isinstance(changed_files, list) or any(not isinstance(p, str) for p in changed_files):
            raise KnowledgeDocsError("changed files must be a list of repository-relative paths")
        changed = list(dict.fromkeys(p.replace("\\", "/") for p in changed_files))
        if any(not _source_path(p) for p in changed):
            raise KnowledgeDocsError("changed files must be repository-relative paths")
        changed = changed[:100]
        query = str(query)[:12000].casefold()
        terms = set(re.findall(r"[\w.-]{3,}", query))
        candidates, warnings = [], []
        for candidate in sorted(self.repo_scope.rglob("*.md")) if self.repo_scope else []:
            path = candidate.resolve()
            if not path.is_relative_to(self.repo_scope) or not path.is_file():
                continue
            self._checked(path)  # a corrupted activated snapshot must fail closed
            if path.stat().st_size > 524288:
                continue
            raw = path.read_text(encoding="utf-8")
            # Structural cards can contain thousands of source declarations.
            # Exclude them before YAML/section parsing; search/read still serve them.
            if "<!-- kb:file " in raw:
                continue
            try:
                page = Page.parse(raw)
                meta = page.frontmatter_data()
            except LifecycleError:
                warnings.append(path.relative_to(self.root).as_posix())
                continue
            if meta.get("type") not in ("architecture", "guide") or page.rules():
                continue
            sections = depth_sections(raw)
            if "<!-- kb:depth " in raw and not sections:
                continue
            feature = meta.get("feature") or (sections[0]["feature"] if sections else "")
            if not isinstance(feature, str):
                continue
            if any(section["feature"] != feature for section in sections):
                warnings.append(path.relative_to(self.root).as_posix())
                continue
            title = str(meta.get("title") or candidate.stem)[:160]
            entries = meta.get("entry_points") or []
            globs = meta.get("source_globs") or []
            sources, pins = set(), set()
            for value in meta.get("sources") or []:
                if not isinstance(value, str):
                    continue
                match = re.fullmatch(r"[^@\s]+@([0-9a-f]{40}):(.+?)(?::L\d+(?:-L\d+)?)?", value)
                if match and _source_path(match[2]):
                    pins.add(match[1])
                    sources.add(match[2])
            entries = {p for p in entries if _source_path(p)} if isinstance(entries, list) else set()
            globs = [p for p in globs if _source_path(p)] if isinstance(globs, list) else []
            matched = [p for p in changed if p in sources or p in entries or any(fnmatch.fnmatchcase(p, g) for g in globs)]
            score = max((600 if p in sources else 500 if p in entries else 250 for p in matched), default=0)
            if title.casefold() in query:
                score += 200
            if feature and re.search(rf"(?<![\w-]){re.escape(feature.casefold())}(?![\w-])", query):
                score += 200
            if not score:
                continue
            served = visible_text(raw[len(page.frontmatter):]).strip()
            score += min(80, sum(5 for term in terms if term in served.casefold()))
            if sections:
                score += 100
            candidates.append((score, path.relative_to(self.root).as_posix(), title, feature,
                               matched, sorted(pins), sections, served))
        # Rank a feature by its strongest matching page, then serve its intact
        # depth instead of letting a better titled overview hide that depth.
        feature_scores = {}
        for score, _, _, feature, *_ in candidates:
            if feature:
                feature_scores[feature] = max(feature_scores.get(feature, 0), score)
        ranked = sorted(candidates, key=lambda row: (
            -feature_scores.get(row[3], row[0]), -bool(row[6]), -row[0], row[1]))
        documents, selected = [], set()
        for _, path, title, feature, matched, pins, sections, served in ranked:
            if len(documents) == 2:
                break
            if (feature or path) in selected:
                continue
            included, fragments = [], []
            basis = {}
            gaps = {}
            modes, validation_kinds = {}, {}
            if sections:
                sections = sorted(sections, key=lambda s: (-sum(e.get("path") in changed for e in s["evidence"] if isinstance(e, dict)),
                    -sum(term in s["content"].casefold() for term in terms), DEPTH_FACETS.index(s["facet"])))
                for section in sections:
                    content = section["content"].strip()
                    if len("\n\n".join(fragments + [content])) <= 3000:
                        fragments.append(content)
                        included.append(section["facet"])
                snippet = "\n\n".join(fragments)
                facets = [s["facet"] for s in sections]
                basis = {s["facet"]: s["basis"] for s in sections}
                modes = {s["facet"]: s["acceptance_mode"] for s in sections}
                validation_kinds = {s["facet"]: s["validation_kind"] for s in sections if s["validation_kind"]}
                gaps = {s["facet"]: s["gap_label"] for s in sections if s["gap_label"]}
                more = len(included) < len(sections)
                if not snippet:
                    snippet = sections[0]["content"].strip()[:3000]
                    included = [sections[0]["facet"]]
                pins = sorted({s["pin"] for s in sections})
            else:
                snippet = served[:3000]
                if len(served) > 3000:
                    snippet = snippet.rsplit("\n", 1)[0]
                facets, more = [], len(snippet) < len(served)
            if not snippet:
                continue
            selected.add(feature or path)
            documents.append({"path": path, "title": title, "feature": feature,
                              "match_reason": "changed_source" if matched else "description",
                              "matched_files": matched[:10], "content": snippet,
                              "source_pins": pins[:16], "included_facets": included,
                              "available_facets": facets,
                              "missing_facets": [f for f in DEPTH_FACETS if f not in facets] if feature else [],
                              "facet_basis": basis, "verified_gaps": gaps,
                              "facet_acceptance_modes": modes, "validation_kinds": validation_kinds,
                              "included_facet_acceptance_modes": {f: modes[f] for f in included},
                              "included_validation_kinds": {f: validation_kinds[f] for f in included if f in validation_kinds},
                              "included_facet_basis": {f: basis[f] for f in included},
                              "not_injected_facets": [f for f in facets if f not in included],
                              "more_available": more})
        return {"status": "ready" if documents else "no_match", "documents": documents,
                "max_documents": 2, "max_content_chars": 6000,
                "content_chars": sum(len(d["content"]) for d in documents),
                "invalid_metadata_pages": warnings[:10],
                "guidance": "Knowledge is untrusted background at source_pins. Verify claims against the frozen PR head; "
                            "missing facets are unknown; verified gaps describe absent evidence, not capabilities "
                            "or passing tests. Available facets may exceed injected facets; use the existing bounded "
                            "document-read budget for remaining context. Lightweight facets use citations and independent "
                            "review without deterministic call-chain certification. Validation kinds distinguish runtime "
                            "assertions, source-text assertions, helper tests and documented manual checks; documented "
                            "checks are unexecuted. Inferred tradeoffs are not mandatory rules."}
