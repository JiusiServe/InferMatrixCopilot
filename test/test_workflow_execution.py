"""Shared execution must preserve resources and refuse unproven resumptions."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from infermatrix_copilot.app.workflow_execution import WorkflowExecution
from infermatrix_copilot.engine import StepRegistry, StepResult, StepSpec
from infermatrix_copilot.engine.lifecycle import RunLock, RunLockHeld, register_finalizer
from infermatrix_copilot.playbooks.store import Playbook, PlaybookStep


def workflow(*steps):
    return Playbook(name="bound", version=1, status="active", task_kinds=["pr_review"],
                    repos=[], steps=[PlaybookStep(name, name) for name in steps])


def test_embedded_execution_uses_default_retry_bound_without_full_app_settings(tmp_path):
    registry, visits = StepRegistry(), []

    async def handler(ctx):
        visits.append(True)
        return StepResult(True)

    registry.register(StepSpec("inspect", "deterministic", "read", handler))
    result = asyncio.run(WorkflowExecution(SimpleNamespace(), registry).execute(
        workflow("inspect"), run_dir=tmp_path, state={}))
    assert result.status == "done" and len(visits) == 1


def test_runtime_is_per_execution_and_never_checkpointed(settings, tmp_path):
    registry = StepRegistry()
    seen = []

    async def handler(ctx):
        await asyncio.sleep(0)
        seen.append(ctx.runtime)
        return StepResult(True, outputs={"value": ctx.runtime["value"]})

    registry.register(StepSpec("inspect", "deterministic", "read", handler))
    execution = WorkflowExecution(settings, registry)
    runtimes = [{"value": "one", "secret": object()}, {"value": "two", "secret": object()}]

    async def run():
        return await asyncio.gather(*[
            execution.execute(workflow("inspect"), run_dir=tmp_path / str(i), state={}, runtime=runtime)
            for i, runtime in enumerate(runtimes)
        ])

    assert all(outcome.status == "done" for outcome in asyncio.run(run()))
    assert seen == runtimes
    assert "secret" not in (tmp_path / "0" / "progress.json").read_text()


def test_preflight_always_runs_before_cached_replay(settings, tmp_path):
    registry, events = StepRegistry(), []

    async def preflight(ctx):
        events.append("preflight")
        return StepResult(True)

    async def build(ctx):
        events.append("build")
        return StepResult(True, outputs={"state_updates": {"accepted": True}})

    registry.register(StepSpec("prepare", "validation", "read", preflight, checkpoint=False))
    registry.register(StepSpec("build", "agent", "read", build))
    execution = WorkflowExecution(settings, registry)
    pb = workflow("prepare", "build")
    assert asyncio.run(execution.execute(pb, run_dir=tmp_path, state={}, fingerprint="batch")).status == "done"
    events.clear()

    def validate(step, outputs):
        events.append("validate")
        assert step == "build" and outputs["state_updates"]["accepted"] is True

    state = {}
    result = asyncio.run(execution.execute(pb, run_dir=tmp_path, state=state,
                                          fingerprint="batch", validate_cached=validate))
    assert result.status == "done" and events == ["preflight", "validate"]
    assert state["accepted"] is True
    assert set(json.loads((tmp_path / "progress.json").read_text())["completed"]) == {"build"}


@pytest.mark.parametrize("stored", ["other", None])
def test_fingerprint_mismatch_preserves_checkpoint_and_never_dispatches(settings, tmp_path, stored):
    progress = {"completed": {"build": {"outputs": {"state_updates": {"accepted": True}}}}}
    if stored:
        progress["fingerprint"] = stored
    path = tmp_path / "progress.json"
    path.write_text(json.dumps(progress))
    original = path.read_bytes()
    registry = StepRegistry()

    async def forbidden(ctx):
        pytest.fail("unbound checkpoint must not dispatch")

    registry.register(StepSpec("build", "agent", "read", forbidden))
    state = {}
    result = asyncio.run(WorkflowExecution(settings, registry).execute(
        workflow("build"), run_dir=tmp_path, state=state, fingerprint="batch"))
    assert result.status == "blocked" and "fingerprint" in result.blocked_reason
    assert "accepted" not in state and path.read_bytes() == original


def test_cached_validation_refuses_before_replaying_state(settings, tmp_path):
    path = tmp_path / "progress.json"
    path.write_text(json.dumps({"completed": {"build": {"outputs": {"state_updates": {"accepted": True}}}}}))
    registry = StepRegistry()

    async def handler(ctx):
        pytest.fail("corrupt cached artifact must not be regenerated")

    registry.register(StepSpec("build", "agent", "read", handler))

    def validate(step, outputs):
        raise ValueError("artifact missing")

    state = {}
    result = asyncio.run(WorkflowExecution(settings, registry).execute(
        workflow("build"), run_dir=tmp_path, state=state, validate_cached=validate))
    assert result.status == "blocked" and "artifact missing" in result.blocked_reason
    assert "accepted" not in state


@pytest.mark.parametrize("cached", [42, {"outputs": []}, {"outputs": {"state_updates": []}}])
def test_malformed_cached_result_blocks_without_dispatch(settings, tmp_path, cached):
    (tmp_path / "progress.json").write_text(json.dumps({"completed": {"build": cached}}))
    registry = StepRegistry()

    async def handler(ctx):
        pytest.fail("malformed checkpoints cannot authorize dispatch")

    registry.register(StepSpec("build", "agent", "read", handler))
    result = asyncio.run(WorkflowExecution(settings, registry).execute(
        workflow("build"), run_dir=tmp_path, state={}))
    assert result.status == "blocked" and "invalid" in result.blocked_reason


def test_supplied_lock_stays_owned_and_finalizers_run(settings, tmp_path):
    registry, finalized = StepRegistry(), []

    async def fail(ctx):
        async def finish(outcome):
            finalized.append(outcome.status)
        register_finalizer(ctx.run_dir, finish)
        raise ValueError("failed")

    registry.register(StepSpec("fail", "deterministic", "read", fail))
    with RunLock(tmp_path) as held:
        result = asyncio.run(WorkflowExecution(settings, registry).execute(
            workflow("fail"), run_dir=tmp_path, state={}, held_lock=held))
        assert result.status == "blocked" and finalized == ["blocked"]
        with pytest.raises(RunLockHeld):
            RunLock(tmp_path).acquire()
    RunLock(tmp_path).acquire().release()


def test_partial_output_continues_without_a_completed_checkpoint(settings, tmp_path):
    registry, visits = StepRegistry(), []

    async def build(ctx):
        visits.append(ctx.item)
        return StepResult(True, outputs={"state_updates": {"preview": True}},
                          checkpoint=ctx.item != "unfinished")

    async def inspect(ctx):
        assert ctx.state["preview"] is True
        return StepResult(True, checkpoint=False)

    registry.register(StepSpec("build", "agent", "read", build))
    registry.register(StepSpec("inspect", "validation", "read", inspect))
    pb = workflow("build", "inspect")
    pb.steps[0].foreach = "items"
    execution = WorkflowExecution(settings, registry)
    for _ in range(2):
        result = asyncio.run(execution.execute(pb, run_dir=tmp_path,
                                               state={"items": ["accepted", "unfinished"]}))
        assert result.status == "done"
    assert visits == ["accepted", "unfinished", "accepted", "unfinished"]
    assert not (tmp_path / "progress.json").exists()
