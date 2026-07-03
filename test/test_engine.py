import asyncio

import pytest

from omni_copilot.engine import Executor, FailureKind, StepRegistry, StepResult, StepSpec
from omni_copilot.notify import Notifier
from omni_copilot.playbooks.store import Playbook, PlaybookStep


def make_step(name, fn, risk="read"):
    async def handler(ctx):
        return fn(ctx)
    return StepSpec(name, "deterministic", risk, handler)


def playbook(steps, name="test-pb"):
    return Playbook(name=name, version=1, status="active", task_kinds=["pr_review"],
                    repos=[], steps=steps)


@pytest.fixture()
def env(settings, trace, tmp_path):
    run_dir = tmp_path / "run"
    registry = StepRegistry()
    notifier = Notifier(settings, run_dir, trace, "run-test")
    executor = Executor(registry, settings, run_dir=run_dir, trace=trace,
                        notifier=notifier)
    return registry, executor, notifier


def test_sequential_execution_and_outputs(env):
    registry, executor, _ = env
    calls = []
    registry.register(make_step("s.one", lambda ctx: (calls.append("one"),
                       StepResult(True, summary="one done", outputs={"v": 1}))[1]))
    registry.register(make_step("s.two", lambda ctx: (calls.append("two"),
                       StepResult(True, summary=f"got {ctx.state['outputs']['a']['v']}"))[1]))
    pb = playbook([PlaybookStep("a", "s.one"), PlaybookStep("b", "s.two")])
    outcome = asyncio.run(executor.run(pb, {}))
    assert outcome.status == "done"
    assert calls == ["one", "two"]
    assert outcome.step_results["b"].summary == "got 1"


def test_checkpoint_resume_skips_completed(env):
    registry, executor, _ = env
    counter = {"n": 0}

    def flaky(ctx):
        counter["n"] += 1
        if counter["n"] == 1:
            return StepResult(False, FailureKind.TEST_FAILURE, "boom")
        return StepResult(True, summary="ok")

    registry.register(make_step("s.stable", lambda ctx: StepResult(True, summary="stable")))
    registry.register(make_step("s.flaky", flaky))
    pb = playbook([PlaybookStep("a", "s.stable"), PlaybookStep("b", "s.flaky")])

    first = asyncio.run(executor.run(pb, {}))
    assert first.status == "failed"
    second = asyncio.run(executor.run(pb, {}))
    assert second.status == "done"
    assert second.step_results["a"].summary == "stable"  # cached summary, not re-run
    assert counter["n"] == 2  # flaky ran twice, stable once


def test_retryable_is_retried(env):
    registry, executor, _ = env
    attempts = {"n": 0}

    def transient(ctx):
        attempts["n"] += 1
        if attempts["n"] < 2:
            return StepResult(False, FailureKind.RETRYABLE, "transient")
        return StepResult(True, summary="recovered")

    registry.register(make_step("s.transient", transient))
    outcome = asyncio.run(executor.run(playbook([PlaybookStep("a", "s.transient")]), {}))
    assert outcome.status == "done" and attempts["n"] == 2


def test_blocked_escalates(env, tmp_path):
    registry, executor, notifier = env
    registry.register(make_step(
        "s.blocked", lambda ctx: StepResult(False, FailureKind.BLOCKED, "no gpu")))
    outcome = asyncio.run(executor.run(playbook([PlaybookStep("a", "s.blocked")]), {}))
    assert outcome.status == "blocked"
    assert len(notifier.sent) == 1 and "no gpu" in notifier.sent[0].reason
    assert (tmp_path / "run" / "ESCALATION.md").exists()


def test_escalation_summary_and_artifacts_forwarded(env):
    registry, executor, notifier = env
    registry.register(make_step(
        "s.rich_fail", lambda ctx: StepResult(
            False, FailureKind.ESCALATE, "module failed",
            outputs={"escalation_summary": {"module": "scheduler", "exit_code": 1},
                     "artifacts": ["/logs/module-scheduler.log"]})))
    outcome = asyncio.run(executor.run(playbook([PlaybookStep("a", "s.rich_fail")]), {}))
    assert outcome.status == "blocked"
    esc = notifier.sent[0]
    assert esc.state_summary["module"] == "scheduler"
    assert "/logs/module-scheduler.log" in esc.artifacts


def test_foreach_fanout(env):
    registry, executor, _ = env
    seen = []
    registry.register(make_step(
        "s.item", lambda ctx: (seen.append(ctx.item),
                               StepResult(True, summary=str(ctx.item)))[1]))
    pb = playbook([PlaybookStep("a", "s.item", foreach="modules")])
    outcome = asyncio.run(executor.run(pb, {"modules": ["m1", "m2", "m3"]}))
    assert outcome.status == "done"
    assert sorted(seen) == ["m1", "m2", "m3"]
    assert "all 3 items ok" in outcome.step_results["a"].summary


def test_handler_exception_becomes_blocked(env):
    registry, executor, _ = env

    def boom(ctx):
        raise RuntimeError("bug in handler")

    registry.register(make_step("s.boom", boom))
    outcome = asyncio.run(executor.run(playbook([PlaybookStep("a", "s.boom")]), {}))
    assert outcome.status == "blocked"
    assert "bug in handler" in outcome.blocked_reason
