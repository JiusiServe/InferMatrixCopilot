import asyncio

from infermatrix_copilot.engine.steps import register_builtin_steps
from infermatrix_copilot.engine.executor import Executor
from infermatrix_copilot.engine.registry import StepRegistry
from infermatrix_copilot.engine.step import FailureKind, StepContext
from infermatrix_copilot.notify import Notifier
from infermatrix_copilot.push import PushPolicy, guard_push


def test_guard_push_matrix():
    protected = ["main"]
    # default policy: not allowed
    assert not guard_push(PushPolicy(), protected).allowed
    # allowed to a feature branch
    d = guard_push(PushPolicy(allowed=True, branch="dev/vllm-align"), protected)
    assert d.allowed and d.command == ("git", "push", "origin", "HEAD:dev/vllm-align")
    # force-with-lease to a PR head branch
    d = guard_push(PushPolicy(allowed=True, branch="pr-7-fix", force_with_lease=True),
                   protected)
    assert d.allowed and "--force-with-lease" in d.command
    # never to protected branches — even plain push, and force is spelled out
    assert not guard_push(PushPolicy(allowed=True, branch="main"), protected).allowed
    d = guard_push(PushPolicy(allowed=True, branch="main", force_with_lease=True), protected)
    assert not d.allowed and "force-push" in d.reason


def _ctx(settings, trace, tmp_path, state=None, params=None, llm=None):
    return StepContext(settings=settings, state=state or {}, params=params or {},
                       run_dir=tmp_path, trace=trace, llm=llm)


def test_push_step_dry_run_and_forbidden(settings, trace, tmp_path, git_repo):
    registry = register_builtin_steps(StepRegistry())
    push = registry.get("ci.push")

    # forbidden by default policy
    ctx = _ctx(settings, trace, tmp_path,
               state={"repo_path": str(git_repo), "push_policy": PushPolicy()})
    result = asyncio.run(push.handler(ctx))
    assert not result.ok and result.failure is FailureKind.FORBIDDEN

    # allowed but ALLOW_PUSH=0 -> dry-run, nothing executed
    ctx = _ctx(settings, trace, tmp_path, state={
        "repo_path": str(git_repo),
        "push_policy": PushPolicy(allowed=True, branch="feature/x"),
    })
    result = asyncio.run(push.handler(ctx))
    assert result.ok and result.outputs.get("dry_run") is True
    assert any(True for _ in trace.events("push_requested"))


def test_guard_clean_step(settings, trace, tmp_path, git_repo):
    registry = register_builtin_steps(StepRegistry())
    guard = registry.get("workspace.guard_clean")

    ctx = _ctx(settings, trace, tmp_path, state={"repo_path": str(git_repo)})
    assert asyncio.run(guard.handler(ctx)).ok

    (git_repo / "dirty.txt").write_text("x")
    result = asyncio.run(guard.handler(ctx))
    assert not result.ok and result.failure is FailureKind.BLOCKED


def test_external_rebase_step_runs_command(settings, trace, tmp_path):
    registry = register_builtin_steps(StepRegistry())
    step = registry.get("rebase.run_external")
    ctx = _ctx(settings, trace, tmp_path, params={"command": "echo hello-rebase"})
    result = asyncio.run(step.handler(ctx))
    assert result.ok and "hello-rebase" in result.outputs["tail"]

    # exit 1 with no parent state.json at all -> blocked at/before init
    ctx = _ctx(settings, trace, tmp_path, params={"command": "false"})
    result = asyncio.run(step.handler(ctx))
    assert not result.ok and result.failure is FailureKind.BLOCKED


def test_agent_step_blocked_without_llm(settings, trace, tmp_path):
    registry = register_builtin_steps(StepRegistry())
    step = registry.get("agent.review_diff")
    ctx = _ctx(settings, trace, tmp_path, state={"diff_text": "diff --git ..."})
    result = asyncio.run(step.handler(ctx))
    assert not result.ok and result.failure is FailureKind.BLOCKED
