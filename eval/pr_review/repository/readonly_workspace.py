"""Ephemeral repository snapshot containing no review-after commits."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from types import TracebackType

from .snapshot import GitSnapshotError, verify_commit


class ReadOnlyWorkspace:
    """Fetch only base/head reachable objects into an isolated detached checkout.

    A normal worktree shares the bare cache's complete object database, which can
    expose review-after commits through creative read-only Git commands. This
    snapshot uses the local ``file://`` transport so Git transfers only objects
    reachable from the authorized SHAs. The checkout is then made read-only.
    """

    def __init__(
        self,
        repo: str | Path,
        head_sha: str,
        *,
        base_sha: str | None = None,
        parent: str | Path | None = None,
    ):
        self.repo = Path(repo).resolve()
        self.head_sha = head_sha
        self.base_sha = base_sha
        self.parent = Path(parent).resolve() if parent else None
        self.path: Path | None = None

    def __enter__(self) -> Path:
        head = verify_commit(self.repo, self.head_sha)
        base = verify_commit(self.repo, self.base_sha) if self.base_sha else None
        root = Path(tempfile.mkdtemp(prefix="pr-review-", dir=self.parent))
        workspace = root / "workspace"
        workspace.mkdir()
        try:
            self._run(["git", "init", "--quiet", str(workspace)])
            refspecs = [f"{head}:refs/eval/head"]
            if base and base != head:
                refspecs.append(f"{base}:refs/eval/base")
            self._run([
                "git", "-C", str(workspace),
                "-c", "protocol.file.allow=always",
                "fetch", "--quiet", "--no-tags", self.repo.as_uri(), *refspecs,
            ])
            self._run(["git", "-C", str(workspace), "checkout", "--quiet", "--detach", "refs/eval/head"])
            self.path = workspace
            self._set_read_only(workspace)
            return workspace
        except Exception:
            shutil.rmtree(root, ignore_errors=True)
            raise

    @staticmethod
    def _run(argv: list[str]) -> None:
        proc = subprocess.run(argv, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            raise GitSnapshotError(proc.stderr.strip() or "git snapshot command failed")

    def _set_read_only(self, root: Path) -> None:
        for current, dirs, files in os.walk(root):
            for name in dirs + files:
                path = Path(current) / name
                try:
                    mode = stat.S_IMODE(path.lstat().st_mode)
                    path.chmod(mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
                except (FileNotFoundError, PermissionError):
                    continue
        mode = stat.S_IMODE(root.lstat().st_mode)
        root.chmod(mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)

    def _restore_write_for_cleanup(self, root: Path) -> None:
        root.chmod(stat.S_IMODE(root.lstat().st_mode) | stat.S_IWUSR)
        for current, dirs, files in os.walk(root):
            for name in dirs + files:
                path = Path(current) / name
                try:
                    mode = stat.S_IMODE(path.lstat().st_mode)
                    path.chmod(mode | stat.S_IWUSR)
                except (FileNotFoundError, PermissionError):
                    continue

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self.path is None:
            return
        root = self.path.parent
        self._restore_write_for_cleanup(self.path)
        shutil.rmtree(root, ignore_errors=True)
