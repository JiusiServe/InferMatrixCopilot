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
    for root in _CANDIDATES:
        if root and (Path(root) / "agent/lib/checkout_lock.py").is_file():
            spec = importlib.util.spec_from_file_location(
                "ext1_checkout_lock",
                Path(root) / "agent/lib/checkout_lock.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    return None


guard = _external_guard()
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