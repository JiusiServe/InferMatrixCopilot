"""A frozen, committed Git range used by the PR patch and push gates."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class ChangeSetError(ValueError):
    """The intended committed change cannot be established safely."""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ChangeSetError(f"git {' '.join(args)} failed: {exc}") from exc


@dataclass(frozen=True)
class ChangeSet:
    base_sha: str
    head_sha: str
    diff_text: str

    @classmethod
    def capture(cls, repo_path: str | Path, base_ref: str) -> "ChangeSet":
        """Read exactly the commits a subsequent `git push HEAD` can publish."""
        repo = Path(repo_path)
        if not base_ref:
            raise ChangeSetError("pre-push review needs an explicit base ref")
        dirty = _git(repo, "diff", "--quiet", "HEAD")
        if dirty.returncode != 0:
            if dirty.returncode == 1:
                raise ChangeSetError("commit tracked workspace edits before pre-push review")
            raise ChangeSetError(f"cannot inspect workspace: {dirty.stderr[:300]}")
        resolved = []
        for ref in (base_ref, "HEAD"):
            result = _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
            if result.returncode != 0:
                raise ChangeSetError(f"cannot resolve review ref {ref!r}: {result.stderr[:300]}")
            resolved.append(result.stdout.strip())
        base_sha, head_sha = resolved
        diff = _git(repo, "diff", "--no-ext-diff", "--binary", base_sha, head_sha)
        if diff.returncode != 0:
            raise ChangeSetError(f"cannot read committed diff: {diff.stderr[:300]}")
        return cls(base_sha=base_sha, head_sha=head_sha, diff_text=diff.stdout)
