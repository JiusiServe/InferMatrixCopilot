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