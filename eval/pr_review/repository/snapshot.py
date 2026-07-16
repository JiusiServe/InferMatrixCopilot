"""Read-only access to fixed Git snapshots."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitSnapshotError(RuntimeError):
    pass


def run_git(repo: str | Path, *args: str, max_bytes: int = 2_000_000) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise GitSnapshotError(proc.stderr.decode("utf-8", errors="replace").strip())
    if len(proc.stdout) > max_bytes:
        raise GitSnapshotError(f"git output exceeded {max_bytes} bytes")
    return proc.stdout.decode("utf-8", errors="replace")


def verify_commit(repo: str | Path, sha: str) -> str:
    resolved = run_git(repo, "rev-parse", "--verify", f"{sha}^{{commit}}").strip()
    if not resolved:
        raise GitSnapshotError(f"commit not found: {sha}")
    return resolved


def read_file_at(repo: str | Path, sha: str, path: str, *, max_bytes: int = 1_000_000) -> str:
    return run_git(repo, "show", f"{sha}:{path}", max_bytes=max_bytes)


def diff_between(repo: str | Path, base_sha: str, head_sha: str, *, max_bytes: int = 4_000_000) -> str:
    return run_git(repo, "diff", "--no-ext-diff", "--unified=80", base_sha, head_sha, max_bytes=max_bytes)


def merge_base(repo: str | Path, base_sha: str, head_sha: str) -> str:
    value = run_git(repo, "merge-base", base_sha, head_sha).strip()
    if not value:
        raise GitSnapshotError("base/head have no merge base")
    return value


def changed_files_between(repo: str | Path, base_sha: str, head_sha: str) -> list[str]:
    output = run_git(repo, "diff", "--name-only", "--no-renames", base_sha, head_sha)
    return [line for line in output.splitlines() if line]
