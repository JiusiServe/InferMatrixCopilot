"""EXT1 e2e — mutual exclusion between the EXTERNAL orchestrator's
startup flock and the copilot's `CheckoutLock`, in both directions.

The external guard (`agent/lib/checkout_lock.py` in the canonical
vllm-omni-rebase-agent checkout) is deliberately stdlib-only so this
suite can load the FILE directly — no `agent` package import, no
langgraph — and prove the two sides contend on the same
`<checkout>/locks/omni.lock` protocol. Skips cleanly on machines
without the external checkout (the copilot suite stays offline-green
everywhere; this test is inherently about THIS deployment)."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from infermatrix_copilot.config import Settings
from infermatrix_copilot.rebase_engine.runctx import CheckoutLock

_CANDIDATES = [
    Path(os.environ.get("REBASE_AGENT_ROOT", "")),
    Settings.model_fields["rebase_agent_root"].default,
    Path("/data/zhoutaichang/rebase/vllm-omni-rebase-agent"),
]


def _external_guard():
    """(module, root) for the first candidate checkout CARRYING the EXT1
    guard — the presence of checkout_lock.py is what selects the root, so
    every assertion in this file (including source-order checks) reads the
    SAME checkout the guard came from (a stale sibling working copy
    without EXT1 must never be inspected instead)."""
    for root in _CANDIDATES:
        if root and (Path(root) / "agent/lib/checkout_lock.py").is_file():
            spec = importlib.util.spec_from_file_location(
                "ext1_checkout_lock",
                Path(root) / "agent/lib/checkout_lock.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, Path(root)
    return None, None


guard, GUARD_ROOT = _external_guard()
pytestmark = pytest.mark.skipif(
    guard is None, reason="external vllm-omni-rebase-agent checkout (with "
                          "the EXT1 guard) not present on this machine")


def test_mutual_exclusion_both_directions(tmp_path):
    checkout = tmp_path / "omni"
    checkout.mkdir()

    # copilot holds -> external refused
    ours = CheckoutLock(checkout, "omni")
    assert ours.acquire(blocking=False) is True
    assert guard.acquire_checkout_lock(checkout) is False
    ours.release()

    # external holds -> copilot refused; release frees
    assert guard.acquire_checkout_lock(checkout) is True
    probe = CheckoutLock(checkout, "omni")
    assert probe.acquire(blocking=False) is False
    guard.release_checkout_lock()
    assert probe.acquire(blocking=False) is True
    probe.release()

    # both sides lock the SAME file (protocol identity, not coincidence)
    assert ours.path == checkout / "locks" / "omni.lock"
    assert (checkout / "locks" / "omni.lock").exists()


def test_release_leaves_the_file(tmp_path):
    """Deleting a lock file while another process holds its flock would
    break exclusion via a fresh inode — both sides deliberately leave it
    in place."""
    checkout = tmp_path / "omni"
    checkout.mkdir()
    assert guard.acquire_checkout_lock(checkout) is True
    guard.release_checkout_lock()
    assert (checkout / "locks" / "omni.lock").exists()


def test_exclusion_failure_fails_closed(tmp_path):
    """Round-2 P1: on a GIT checkout where the hygiene shield cannot be
    installed, acquisition must FAIL (an unignored lock file faces the
    guard/L2 deletion path) — and must not leave the flock held."""
    import subprocess
    for side in ("external", "copilot"):
        checkout = tmp_path / f"omni-{side}"
        checkout.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
        # make `.git/info` an unwritable location: a FILE where the dir
        # must go -> mkdir raises, the shield cannot install
        import shutil
        shutil.rmtree(checkout / ".git" / "info", ignore_errors=True)
        (checkout / ".git" / "info").write_text("not a dir")
        if side == "external":
            assert guard.acquire_checkout_lock(checkout) is False
        else:
            assert CheckoutLock(checkout, "omni").acquire(
                blocking=False) is False
        # the failed acquisition released the flock
        probe = CheckoutLock(tmp_path / "clean", "omni")
        (tmp_path / "clean").mkdir(exist_ok=True)
        import fcntl
        with open(checkout / "locks" / "omni.lock") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)  # acquirable
            fcntl.flock(fh, fcntl.LOCK_UN)


def test_losing_contender_never_touches_exclude(tmp_path):
    """Round-2 P1: the exclusion write happens UNDER the flock — a losing
    contender must not read-modify-write (and possibly truncate)
    `info/exclude` while the winner is active."""
    import subprocess
    checkout = tmp_path / "omni"
    checkout.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
    winner = CheckoutLock(checkout, "omni")
    assert winner.acquire(blocking=False) is True
    exclude = checkout / ".git" / "info" / "exclude"
    before = exclude.read_bytes()
    sentinel = before + b"# sentinel: losers must not rewrite this file\n"
    exclude.write_bytes(sentinel)
    # both kinds of loser are refused BEFORE any exclude write
    assert guard.acquire_checkout_lock(checkout) is False
    assert CheckoutLock(checkout, "omni").acquire(blocking=False) is False
    assert exclude.read_bytes() == sentinel
    winner.release()


def test_relative_gitdir_resolves_against_dotgit_file(tmp_path):
    """Round-2 P2: a RELATIVE `gitdir:` pointer resolves against the
    directory containing the `.git` file (as git does), never our cwd —
    otherwise a valid worktree layout shields the wrong repository."""
    main_repo = tmp_path / "main"
    (main_repo / ".git" / "worktrees" / "wt").mkdir(parents=True)
    wt = tmp_path / "wt"
    wt.mkdir()
    (wt / ".git").write_text("gitdir: ../main/.git/worktrees/wt\n")
    assert guard.acquire_checkout_lock(wt) is True
    guard.release_checkout_lock()
    common_exclude = main_repo / ".git" / "info" / "exclude"
    assert common_exclude.exists()
    assert "locks/" in common_exclude.read_text().split("\n")
    # the copilot side resolves identically
    wt2 = tmp_path / "wt2"
    wt2.mkdir()
    (wt2 / ".git").write_text("gitdir: ../main/.git/worktrees/wt\n")
    lock = CheckoutLock(wt2, "omni")
    assert lock.acquire(blocking=False) is True
    lock.release()


def test_orchestrator_main_ordering():
    """Round-2 P2: the guard is taken AFTER the dry-run exit and BEFORE
    both baseline detection (checkout READS must not capture another
    holder's intermediate state) and resume detection (the first
    mutation). Pinned against the external main() source and the v1
    runtime builder."""
    src = (GUARD_ROOT / "agent/orchestrator.py").read_text()
    main_src = src[src.index("async def main("):]
    order = [main_src.index("if args.dry_run:"),
             main_src.index("acquire_checkout_lock("),
             main_src.index("settings = detect_baseline(settings)"),
             main_src.index("# Resume detection")]
    assert order == sorted(order), order
    # v1: the in-process backend orders identically
    from infermatrix_copilot.engine.steps import rebase_native
    v1_src = Path(rebase_native.__file__).read_text()
    build_src = v1_src[v1_src.index("def _ensure_runtime("):]
    assert build_src.index("_ensure_omni_lock(ctx, settings)") \
        < build_src.index("orch.detect_baseline(settings)")


def test_lock_survives_workspace_hygiene(tmp_path):
    """The round-1 P1: on a REAL git checkout the live lock file must be
    invisible to every hygiene pass the parent's phase 1 (and the
    copilot's guards) run — `git status` (the clean-tree verdict),
    `git clean -fd` (the L2 dirty-worktree cleanup), and `git add -A`
    (push staging). Both sides write `locks/` into the LOCAL
    `.git/info/exclude` at acquire time; the flock must still be on the
    SAME inode afterwards (a cleaned-and-recreated file would defeat
    mutual exclusion)."""
    import subprocess

    def git(*args):
        return subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=checkout, check=True, capture_output=True, text=True)

    for side, take, drop in (
            ("external", lambda c: guard.acquire_checkout_lock(c),
             lambda: guard.release_checkout_lock()),
            ("copilot", None, None)):
        checkout = tmp_path / f"omni-{side}"
        checkout.mkdir()
        git("init", "-q")
        (checkout / "seed.txt").write_text("s")
        git("add", "-A")
        git("commit", "-qm", "seed")
        if side == "copilot":
            lock = CheckoutLock(checkout, "omni")
            assert lock.acquire(blocking=False) is True
            drop = lock.release
        else:
            assert take(checkout) is True
        lock_file = checkout / "locks" / "omni.lock"
        inode = lock_file.stat().st_ino
        # 1. the clean-tree verdict: nothing to report
        assert git("status", "--porcelain").stdout.strip() == "", side
        # 2. the L2 cleanup: a non-`-x` git clean must not touch it
        git("clean", "-fdq")
        assert lock_file.exists(), side
        assert lock_file.stat().st_ino == inode, side   # SAME inode
        # ...and the flock is still held on it
        probe = CheckoutLock(checkout, "omni")
        assert probe.acquire(blocking=False) is False, side
        # 3. push staging: `git add -A` stages nothing
        git("add", "-A")
        assert git("diff", "--cached", "--name-only").stdout.strip() \
            == "", side
        drop()
        assert probe.acquire(blocking=False) is True, side
        probe.release()