"""Local shared Git cache management; no network is used during an evaluation run."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .snapshot import GitSnapshotError


class RepositoryCache:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, repository: str) -> Path:
        owner, name = repository.split("/", 1)
        return self.root / owner / f"{name}.git"

    def require(self, repository: str) -> Path:
        path = self.path_for(repository)
        if not (path / "HEAD").exists():
            raise GitSnapshotError(f"repository cache is missing: {path}")
        return path

    def import_local(self, repository: str, source: str | Path) -> Path:
        """Populate a bare cache from an already available local repository."""
        destination = self.path_for(repository)
        if destination.exists():
            return destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            ["git", "clone", "--bare", "--no-local", str(Path(source).resolve()), str(destination)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if proc.returncode != 0:
            raise GitSnapshotError(proc.stderr.strip())
        return destination
