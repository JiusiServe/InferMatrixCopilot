"""Filesystem path guard for benchmark and workspace isolation."""

from __future__ import annotations

from pathlib import Path


class AccessViolation(PermissionError):
    pass


class AccessGuard:
    def __init__(self, workspace: str | Path, *, forbidden_roots: list[str | Path] | None = None):
        self.workspace = Path(workspace).resolve()
        self.forbidden_roots = [Path(root).resolve() for root in (forbidden_roots or [])]

    def resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        resolved = candidate.resolve() if candidate.is_absolute() else (self.workspace / candidate).resolve()
        try:
            resolved.relative_to(self.workspace)
        except ValueError as exc:
            raise AccessViolation(f"path escapes workspace: {path}") from exc
        for root in self.forbidden_roots:
            if resolved == root or root in resolved.parents:
                raise AccessViolation(f"path enters forbidden benchmark data: {path}")
        return resolved
