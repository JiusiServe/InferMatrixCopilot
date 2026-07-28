"""PR0 guardrails: durable progress checkpoints, the same-run lock, and the
finalizer hook point — all behavior-preserving for existing playbooks."""

import asyncio
import json
from pathlib import Path

import pytest

from infermatrix_copilot.engine import lifecycle
from infermatrix_copilot.engine.executor import Executor
from infermatrix_copilot.engine.lifecycle import RunLock, RunLockHeld, run_guarded
from infermatrix_copilot.engine.registry import StepRegistry


@pytest.fixture()
def executor(settings, trace, tmp_path: Path) -> Executor:
    return Executor(StepRegistry(), settings, run_dir=tmp_path / "run", trace=trace)


# -- durable progress.json -----------------------------------------------------

def test_save_progress_atomic_and_clean(executor):
    executor._save_progress({"completed": {"a": {"summary": "ok"}}})
    saved = json.loads(executor.progress_file.read_text())
    assert saved["completed"]["a"]["summary"] == "ok"
    # no tmp residue: the write went through rename, not in-place truncation
    assert list(executor.run_dir.glob("*.tmp")) == []


def test_save_progress_crash_leaves_old_checkpoint(executor, monkeypatch):
    """A crash mid-write (before the rename) must leave the previous checkpoint
    intact — a torn progress.json would strand every resume path."""
    executor._save_progress({"completed": {"a": {}}})
    import infermatrix_copilot.engine.executor as ex

    def boom(fd):
        raise OSError("simulated crash during write")

    monkeypatch.setattr(ex.os, "fsync", boom)
    with pytest.raises(OSError):
        executor._save_progress({"completed": {"a": {}, "b": {}}})
    saved = json.loads(executor.progress_file.read_text())
    assert set(saved["completed"]) == {"a"}  # old checkpoint survived


# -- same-run lock -------------------------------------------------------------

def test_run_lock_excludes_second_holder(tmp_path):
    run_dir = tmp_path / "run"
    with RunLock(run_dir):
        with pytest.raises(RunLockHeld):
            RunLock(run_dir).acquire()


def test_run_lock_reacquirable_after_release(tmp_path):
    run_dir = tmp_path / "run"
    RunLock(run_dir).acquire().release()
    with RunLock(run_dir):
        pass  # no raise


# -- finalizer hook point ------------------------------------------------------

def test_finalize_is_noop_when_nothing_registered(tmp_path):
    asyncio.run(lifecycle.finalize(tmp_path / "run", None))  # no raise


def test_finalizers_run_on_success_and_receive_outcome(tmp_path):
    run_dir = tmp_path / "run"
    seen = []

    async def fin(outcome):
        seen.append(outcome)

    lifecycle.register_finalizer(run_dir, fin)

    async def work():
        return "the-outcome"

    result = asyncio.run(run_guarded(work(), run_dir))
    assert result == "the-outcome"
    assert seen == ["the-outcome"]


def test_finalizers_run_when_the_run_raises(tmp_path):
    run_dir = tmp_path / "run"
    seen = []

    async def fin(outcome):
        seen.append(outcome)

    lifecycle.register_finalizer(run_dir, fin)

    async def work():
        raise RuntimeError("executor died")

    with pytest.raises(RuntimeError):
        asyncio.run(run_guarded(work(), run_dir))
    assert seen == [None]  # no outcome existed; finalizer still ran


def test_finalizers_run_exactly_once(tmp_path):
    run_dir = tmp_path / "run"
    seen = []

    async def fin(outcome):
        seen.append(outcome)

    lifecycle.register_finalizer(run_dir, fin)
    asyncio.run(lifecycle.finalize(run_dir, "x"))
    asyncio.run(lifecycle.finalize(run_dir, "y"))  # consumed: second is a no-op
    assert seen == ["x"]


def test_finalizer_exception_never_masks_the_outcome(tmp_path):
    run_dir = tmp_path / "run"
    ran = []

    async def bad(outcome):
        raise RuntimeError("finalizer bug")

    async def good(outcome):
        ran.append(True)

    lifecycle.register_finalizer(run_dir, bad)
    lifecycle.register_finalizer(run_dir, good)

    async def work():
        return 42

    assert asyncio.run(run_guarded(work(), run_dir)) == 42
    assert ran == [True]  # sibling still ran after the buggy one
