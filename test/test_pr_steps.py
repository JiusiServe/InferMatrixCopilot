import asyncio
import subprocess
from pathlib import Path

import pytest

from omni_copilot.engine.builtin_steps import register_builtin_steps
from omni_copilot.engine.pr_steps import extract_signature
from omni_copilot.engine.registry import StepRegistry
from omni_copilot.engine.step import FailureKind, StepContext
from omni_copilot.targets.base import PushPolicy


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=repo, check=True,
                         capture_output=True, text=True)
    return out.stdout.strip()


@pytest.fixture()
def pr_repos(tmp_path):
    """origin repo with main + a 'feature' PR branch, and a working clone."""
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(origin, "init", "-q", "-b", "main")
    _git(origin, "config", "user.email", "t@e.c")
    _git(origin, "config", "user.name", "t")
    (origin / "core.py").write_text("x = 1\n")
    (origin / "docs.md").write_text("# docs\n")
    _git(origin, "add", ".")
    _git(origin, "commit", "-q", "-m", "base")
    _git(origin, "checkout", "-q", "-b", "feature")
    (origin / "feature.py").write_text("f = 1\n")
    _git(origin, "add", ".")
    _git(origin, "commit", "-q", "-m", "pr change")
    _git(origin, "checkout", "-q", "main")

    work = tmp_path / "work"
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True,
                   capture_output=True)
    _git(work, "config", "user.email", "t@e.c")
    _git(work, "config", "user.name", "t")
    return origin, work


def _ctx(settings, trace, tmp_path, state, params=None, llm=None):
    return StepContext(settings=settings, state=state, params=params or {},
                       run_dir=tmp_path / "rundir", trace=trace, llm=llm)


@pytest.fixture()
def registry():
    return register_builtin_steps(StepRegistry())


def test_checkout_sets_branch_and_push_policy(registry, settings, trace, tmp_path, pr_repos):
    _, work = pr_repos
    state = {"repo_path": str(work), "task_spec": {"pr": 7},
             "pr_meta": {"headRefName": "feature", "baseRefName": "main",
                         "remote": "origin"}}
    step = registry.get("pr.checkout_branch")
    result = asyncio.run(step.handler(_ctx(settings, trace, tmp_path, state,
                                           params={"force_push": True})))
    assert result.ok, result.summary
    assert _git(work, "branch", "--show-current") == "pr-7-feature"
    policy = state["push_policy"]
    assert isinstance(policy, PushPolicy)
    assert policy.allowed and policy.branch == "feature" and policy.force_with_lease


def test_checkout_report_only_disallows_push(registry, settings, trace, tmp_path, pr_repos):
    _, work = pr_repos
    state = {"repo_path": str(work), "task_spec": {"pr": 7, "report_only": True},
             "pr_meta": {"headRefName": "feature", "remote": "origin"}}
    step = registry.get("pr.checkout_branch")
    assert asyncio.run(step.handler(_ctx(settings, trace, tmp_path, state))).ok
    assert state["push_policy"].allowed is False


def test_clean_rebase_and_analyze(registry, settings, trace, tmp_path, pr_repos):
    origin, work = pr_repos
    # advance origin main with a NON-conflicting commit
    (origin / "other.py").write_text("o = 1\n")
    _git(origin, "add", ".")
    _git(origin, "commit", "-q", "-m", "main moves on")

    state = {"repo_path": str(work), "task_spec": {"pr": 7},
             "pr_meta": {"headRefName": "feature", "remote": "origin"}}
    for name in ("pr.checkout_branch", "pr.rebase_onto_base", "pr.analyze_diff"):
        result = asyncio.run(registry.get(name).handler(
            _ctx(settings, trace, tmp_path, state)))
        assert result.ok, f"{name}: {result.summary}"
    # rebased on top of new main: both files reachable
    assert (work / "other.py").exists() and (work / "feature.py").exists()
    analyze = state["affected_modules"]
    assert analyze == ["root"]  # feature.py at top level, no plugin in sandbox
    assert state["primary_files"] == ["*feature.py"]


def test_conflict_without_llm_aborts_and_escalates(registry, settings, trace,
                                                   tmp_path, pr_repos):
    origin, work = pr_repos
    # conflicting change on main touching the same line as a new feature commit
    (origin / "core.py").write_text("x = 2\n")
    _git(origin, "add", ".")
    _git(origin, "commit", "-q", "-m", "main edits core")
    _git(origin, "checkout", "-q", "feature")
    (origin / "core.py").write_text("x = 3\n")
    _git(origin, "add", ".")
    _git(origin, "commit", "-q", "-m", "feature edits core")
    _git(origin, "checkout", "-q", "main")

    state = {"repo_path": str(work), "task_spec": {"pr": 7},
             "pr_meta": {"headRefName": "feature", "remote": "origin"}}
    assert asyncio.run(registry.get("pr.checkout_branch").handler(
        _ctx(settings, trace, tmp_path, state))).ok
    result = asyncio.run(registry.get("pr.rebase_onto_base").handler(
        _ctx(settings, trace, tmp_path, state)))
    assert not result.ok and result.failure is FailureKind.ESCALATE
    assert "core.py" in result.outputs["conflicts"]
    # rebase aborted -> workspace clean, no rebase in progress
    assert _git(work, "status", "--porcelain") == ""
    assert not (work / ".git" / "rebase-merge").exists()
    assert list(trace.events("rebase_conflict"))


def test_extract_signature_prefers_root_cause_over_symptom():
    log = (
        "collecting...\n"
        "E   ImportError: cannot import name 'SchedulerOutput'\n"
        "... later the engine dies ...\n"
        "APIConnectionError: Connection refused\n"
    )
    assert "ImportError" in extract_signature(log)
    assert extract_signature("") == "unknown failure"


def test_group_failures_and_cap(registry, settings, trace, tmp_path):
    failures = [
        {"name": "gpu-test-1", "log": "E   ImportError: cannot import name 'X'"},
        {"name": "gpu-test-2", "log": "blah\nE   ImportError: cannot import name 'X'"},
        {"name": "cpu-test", "log": "AssertionError: bad output"},
    ]
    state = {"ci_failures": failures, "task_spec": {"pr": 7}}
    result = asyncio.run(registry.get("pr.group_failures").handler(
        _ctx(settings, trace, tmp_path, state)))
    assert result.ok
    groups = state["failure_groups"]
    assert len(groups) == 2
    assert sorted(len(g["jobs"]) for g in groups) == [1, 2]

    settings.pr_debug_max_groups = 1
    result = asyncio.run(registry.get("pr.group_failures").handler(
        _ctx(settings, trace, tmp_path, dict(state))))
    assert not result.ok and result.failure is FailureKind.ESCALATE
    assert "safety cap" in result.summary


def test_debug_group_blocked_without_llm(registry, settings, trace, tmp_path):
    state = {"repo_path": "/tmp", "task_spec": {"pr": 7}}
    ctx = _ctx(settings, trace, tmp_path, state)
    ctx.item = {"signature": "E ImportError", "jobs": ["j1"]}
    result = asyncio.run(registry.get("agent.debug_group").handler(ctx))
    assert not result.ok and result.failure is FailureKind.BLOCKED


def test_post_review_gating(registry, settings, trace, tmp_path):
    step = registry.get("pr.post_review")
    # post flag not set -> no-op
    state = {"review_text": "looks fine", "task_spec": {"pr": 7, "post": False}}
    result = asyncio.run(step.handler(_ctx(settings, trace, tmp_path, state)))
    assert result.ok and "not posting" in result.summary
    # post flag set but ALLOW_POST=0 -> dry-run
    state["task_spec"]["post"] = True
    result = asyncio.run(step.handler(_ctx(settings, trace, tmp_path, state)))
    assert result.ok and result.outputs.get("dry_run") is True
    assert "looks fine" in result.outputs["body"]
