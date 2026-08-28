"""PR-time worktrees: identity, materialization, and the hold that keeps a live
run's review tree from being removed under it.

A PR review is pinned to the PR head by materializing a detached worktree at
that commit (`engine/steps/pr/fetch.py`). Three properties this module owns,
each of which was previously missing:

* **Identity.** The destination used to be `<repo.name>-pr<pr>`, keyed on the
  checkout's *directory basename* and the PR number. Two runs on one PR at
  different heads collided on that one path, and the materializer force-removed
  whatever it found there — deleting a live review's tree. Two separately
  configured clones whose directories happen to share a basename (a fork and
  its upstream) collided too, and at the same sha the collision was silent: HEAD
  matched, so the tree was reused and one repository's run read the other's
  files. The key is therefore `<name>-<owner8>-pr<pr>-<sha12>`, where `owner8`
  hashes the *canonical checkout path* — a worktree belongs to exactly one git
  repository, and that path is precisely the ownership boundary.

* **Verification.** The name is a fast key, not proof. Reuse additionally
  requires that the tree's `--git-common-dir` resolve to the requesting
  repository's own git dir and that its HEAD equal the sha. The force-remove
  survives only for a path failing one of those — a foreign or torn tree —
  never for another run's live tree at the same identity.

* **Liveness.** A run keeps a shared (`LOCK_SH`) hold on the destination for as
  long as it uses the tree, so a reaper taking `LOCK_EX | LOCK_NB` skips it.
  This is the only liveness signal that works for every caller: `run_status.json`
  exists solely for MCP-reserved runs, so a CLI review is invisible to it.
  Because `--resume` replays a completed step's `state_updates` instead of
  re-running it, the hold cannot live in the fetch step body; it is attached to
  *use* (`steps/_common.py::repo_path`) and is idempotent.
"""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Callable

from .lifecycle import fcntl, register_finalizer, require_file_locking

def worktree_root() -> Path:
    """The tool's worktree scratch root (`~/.infermatrix-copilot/runs` is its
    sibling). Resolved per call, not at import, so a test that redirects
    `Path.home()` redirects this too."""
    return Path.home() / ".infermatrix-copilot" / "worktrees"

# `git` runner injected by callers (steps/_common.py::git) so this module stays
# free of subprocess policy and is trivially testable.
GitRunner = Callable[..., "tuple[int, str]"]

# canonical destination -> open fd of its shared hold, for this process
_HELD: dict[str, int] = {}


def canonical(path: Path | str) -> str:
    """`path` with `~` expanded and symlinks resolved — the form every key,
    memo and comparison in this module uses."""
    return str(Path(path).expanduser().resolve())


def owner_tag(repo: Path | str) -> str:
    """Short stable tag for the *repository* a worktree belongs to.

    Hashes the canonical checkout path rather than using its basename, so two
    clones in same-named directories get different tags instead of silently
    sharing a tree."""
    return hashlib.sha256(canonical(repo).encode("utf-8")).hexdigest()[:8]


def dest_for(repo: Path | str, pr: int, sha: str, *,
             root: Path | None = None) -> Path:
    """The worktree destination for `(repo, pr, sha)`.

    Distinct heads occupy distinct paths, so the cross-run force-remove is
    unreachable by construction while same-head reuse — the caching this exists
    for — is preserved."""
    base = Path(root) if root is not None else worktree_root()
    return base / f"{Path(repo).name}-{owner_tag(repo)}-pr{int(pr)}-{sha[:12]}"


def lock_path(dest: Path | str) -> Path:
    """The lock file guarding `dest`. A sibling, never a file inside the tree:
    `git worktree remove` would take an inside-the-tree lock with it."""
    return Path(str(Path(dest)) + ".lock")


def _open_lock(dest: Path | str) -> int:
    path = lock_path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    return os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)


def _flock_blocking(fd: int, flags: int, timeout: float) -> bool:
    """Take `flags` on `fd`, retrying until `timeout` seconds elapse.

    `LOCK_EX` here must *block*, not fail: two runs at the same sha racing
    inside `git worktree add` is the ordinary case, and its failure path
    degrades silently to the live checkout — the exact wrong-tree outcome the
    head gate exists to prevent. Polling rather than a blocking flock keeps the
    timeout enforceable."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(fd, flags | fcntl.LOCK_NB)
            return True
        except OSError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.05)


def owned_by(repo: Path, dest: Path, sha: str, git: GitRunner) -> tuple[bool, str]:
    """Whether `dest` is a worktree of `repo` currently at `sha`.

    Both halves matter: the git-dir check catches a tree belonging to a
    different clone that landed on this path, and the HEAD check catches a torn
    or interrupted materialization."""
    code, common = git(dest, "rev-parse", "--git-common-dir")
    if code != 0:
        return False, "not a git worktree"
    # `--git-common-dir` may be relative to `dest`
    common_path = Path(common.strip())
    if not common_path.is_absolute():
        common_path = Path(dest) / common_path
    code, mine = git(repo, "rev-parse", "--git-common-dir")
    if code != 0:
        return False, "requesting repo has no git dir"
    mine_path = Path(mine.strip())
    if not mine_path.is_absolute():
        mine_path = Path(repo) / mine_path
    if canonical(common_path) != canonical(mine_path):
        return False, "worktree belongs to a different repository"
    code, head = git(dest, "rev-parse", "HEAD")
    if code != 0 or head.strip() != sha:
        return False, f"head {head.strip()[:12] or '?'} != {sha[:12]}"
    return True, "owned"


def materialize(repo: Path, sha: str, dest: Path, git: GitRunner, *,
                timeout: float = 300.0) -> tuple[bool, str]:
    """Create (or reuse) a detached worktree of `repo` at `sha` under `dest`,
    serialized by an exclusive hold on `dest`'s lock. Returns `(ok, detail)`;
    never raises for a git-level failure — callers decide whether to block or
    degrade — but a platform without file locking IS raised, because the
    serialization is the guarantee."""
    require_file_locking()
    fd = _open_lock(dest)
    try:
        if not _flock_blocking(fd, fcntl.LOCK_EX, timeout):
            return False, f"worktree lock busy for {timeout:.0f}s"
        try:
            if dest.exists():
                ok, why = owned_by(repo, dest, sha, git)
                if ok:
                    return True, f"reused worktree @ {sha[:12]}"
                # Safe only because the name encodes repo+sha: a mismatch here
                # is a foreign or torn tree, never another run's live one.
                git(repo, "worktree", "remove", "--force", str(dest))
                if dest.exists():
                    return False, f"stale worktree not removable ({why})"
            dest.parent.mkdir(parents=True, exist_ok=True)
            code, out = git(repo, "worktree", "add", "--detach", str(dest), sha)
            if code != 0:
                return False, f"worktree add failed: {out[:300]}"
            return True, f"created worktree @ {sha[:12]}"
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError as exc:
        return False, f"worktree error: {exc}"
    finally:
        os.close(fd)


def hold(dest: Path | str, run_dir: Path) -> bool:
    """Take this process's shared hold on `dest` for the rest of the run.

    Idempotent: repeated calls (every `repo_path(ctx)` in every downstream step,
    on the first run and again after `--resume`) do nothing once held. The hold
    is released by a run finalizer on every exit path, and by the kernel anyway
    if the process dies, so a crashed run never pins a tree forever."""
    key = canonical(dest)
    if key in _HELD or fcntl is None:
        return key in _HELD
    fd = _open_lock(dest)
    try:
        fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
    except OSError:
        # A reaper's exclusive sweep is in flight. Not fatal: the tree is either
        # about to go and the run will rebuild it, or the sweep will skip it.
        os.close(fd)
        return False
    _HELD[key] = fd
    register_finalizer(run_dir, _releaser(key))
    return True


def _releaser(key: str):
    async def _release(_outcome) -> None:
        """Drop the hold and forget it, so a second run in this process (the CLI
        task queue) re-acquires rather than trusting a stale memo."""
        fd = _HELD.pop(key, None)
        if fd is None:
            return
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    return _release


def held_paths() -> list[str]:
    """Canonical destinations this process currently holds (tests/diagnostics)."""
    return sorted(_HELD)
