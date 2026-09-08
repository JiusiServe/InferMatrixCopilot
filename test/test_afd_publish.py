"""Local-rebase publication over real local repositories; no external transport."""

import asyncio
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.engine.executor import Executor, _eval_when
from infermatrix_copilot.engine.registry import StepRegistry
from infermatrix_copilot.engine.step import StepContext
from infermatrix_copilot.engine.steps import register_builtin_steps, rebase_v3
from infermatrix_copilot.rebase_engine import push_to_ci
from infermatrix_copilot.rebase_engine.dependency_lock import check_uv_dependency
from infermatrix_copilot.rebase_engine.modes import mode_state_flags
from infermatrix_copilot.rebase_engine.push_gate import evaluate_push_gate
from infermatrix_copilot.rebase_engine.substate import Substate
from infermatrix_copilot.run_trace import RunTrace

ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          text=True, capture_output=True).stdout.strip()


@pytest.fixture()
def publication(tmp_path, settings, monkeypatch):
    repo, remote, run = tmp_path / "repo", tmp_path / "remote.git", tmp_path / "run"
    repo.mkdir()
    run.mkdir()
    git(repo, "init", "-q", "-b", "codex/afd-sync")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "module.py").write_text("value = 1\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "baseline")
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    git(repo, "remote", "add", "fork", str(remote))
    (repo / "module.py").write_text("value = 2\n")
    manifest = {"push": {"default_remote": "fork", "remote_url": str(remote),
                         "rebase_branch": "codex/afd-sync", "allowed": True,
                         "rebase_branch_allowed": True,
                         "protected_branches": ["main"],
                         "signoff": {"name": "Fixture",
                                     "email": "fixture@example.invalid"}}}
    monkeypatch.setattr(rebase_v3, "_adapter_manifest", lambda ctx: manifest)
    monkeypatch.setattr(rebase_v3, "_ensure_checkout_locks", lambda *args: None)
    settings.allow_push = True
    settings.github_token = ""
    sub = Substate(run, "publication")
    sub.update({"upstream_commit": "a" * 40, "tests": {
        "pipeline": {"complete": True, "passed": 2, "failed": 0,
                     "failed_tests": []},
        "precommit": {"result": "passed"}, "infra_failures": []}})
    ctx = StepContext(settings, {"run_id": "publication", "repo_path": str(repo),
                      "upstream_target_sha": "a" * 40,
                      "afd_validation_sha": git(repo, "rev-parse", "HEAD"),
                      "afd_validation_worktree_digest": rebase_v3._worktree_digest(repo),
                      "task_spec": {"params": {"rebase_mode": "local_rebase"}}},
                      {}, run, RunTrace(run / "trace.jsonl"))
    return SimpleNamespace(repo=repo, remote=remote, run=run, ctx=ctx,
                           sub=sub, manifest=manifest)


def executor_for(env):
    registry = register_builtin_steps(StepRegistry())
    executor = Executor(registry, env.ctx.settings, run_dir=env.run, trace=env.ctx.trace)
    playbook = SimpleNamespace(name="publish-test", steps=[
        SimpleNamespace(id="publish", step="rebase.v3_publish", when="", foreach="",
                        params={}),
        SimpleNamespace(id="finalize", step="rebase.v3_finalize", when="", foreach="",
                        params={})])
    return executor, playbook


def test_shipped_local_rebase_includes_publish_without_remote_ci():
    doc = yaml.safe_load((ROOT / "playbooks/repo-rebase-v3.yaml").read_text())
    flags = mode_state_flags("local_rebase")
    active = [s["id"] for s in doc["steps"]
              if "when" not in s or _eval_when(s["when"], flags)]
    assert active.index("precommit") < active.index("push_gate") < active.index("publish")
    assert active.index("publish") < active.index("finalize")
    assert "ci" not in active


def test_failed_push_resumes_without_repeating_adaptation(publication, monkeypatch):
    env = publication
    real_push = push_to_ci.commit_and_push
    calls = []

    def fail_once(*args, **kwargs):
        calls.append(True)
        if len(calls) == 1:
            return push_to_ci.PushOutcome(False, reason="temporary transport failure")
        return real_push(*args, **kwargs)

    monkeypatch.setattr(push_to_ci, "commit_and_push", fail_once)
    executor, playbook = executor_for(env)
    first = asyncio.run(executor.run(playbook, env.ctx.state))
    assert first.status == "blocked"
    committed = git(env.repo, "rev-parse", "HEAD")
    assert not (env.run / "progress.json").exists()
    resumed = asyncio.run(executor.run(playbook, env.ctx.state))
    assert resumed.status == "done", resumed.blocked_reason
    assert len(calls) == 2
    assert git(env.repo, "rev-parse", "HEAD") == committed
    assert git(env.remote, "rev-parse", "refs/heads/codex/afd-sync") == committed
    assert env.sub.get("push_result") == "pushed"


def test_disabled_push_keeps_local_commit_and_can_resume(publication, monkeypatch):
    env = publication
    env.ctx.settings.allow_push = False
    with monkeypatch.context() as patch:
        patch.setattr(push_to_ci, "commit_and_push",
                      lambda *args, **kwargs: pytest.fail("remote observed without ALLOW_PUSH"))
        result = asyncio.run(rebase_v3._v3_publish(env.ctx))
    assert not result.ok and "ALLOW_PUSH" in result.summary
    assert not git(env.repo, "status", "--porcelain")
    commit = git(env.repo, "rev-parse", "HEAD")
    env.ctx.settings.allow_push = True
    result = asyncio.run(rebase_v3._v3_publish(env.ctx))
    assert result.ok, result.summary
    assert git(env.remote, "rev-parse", "refs/heads/codex/afd-sync") == commit


@pytest.mark.parametrize("change", ["test_failure", "no_tests", "precommit", "module"])
def test_local_publish_cannot_override_incomplete_checks(publication, change):
    env = publication
    data = env.sub.read()
    if change == "test_failure":
        data["tests"]["pipeline"].update(failed=1, failed_tests=["regression"])
    elif change == "no_tests":
        data["tests"]["pipeline"].update(passed=0, complete=False)
    elif change == "precommit":
        data["tests"]["precommit"]["result"] = "failed_preexisting"
    else:
        data["modules"] = {"runtime": {"status": "pending", "skip": False}}
    assert not evaluate_push_gate(data, {"rebase_mode": "local_rebase",
                                         "push_with_failures": True}).allowed


def test_edit_after_validation_stops_before_commit(publication):
    env = publication
    old_head = git(env.repo, "rev-parse", "HEAD")
    (env.repo / "module.py").write_text("value = 3\n")
    result = asyncio.run(rebase_v3._v3_publish(env.ctx))
    assert not result.ok and "changed since validation" in result.summary
    assert git(env.repo, "rev-parse", "HEAD") == old_head


def test_commit_hook_changes_are_not_published(publication):
    env = publication
    hook = env.repo / ".git/hooks/pre-commit"
    hook.write_text("#!/bin/sh\nprintf 'value = 3\\n' > module.py\ngit add module.py\n")
    hook.chmod(0o755)
    result = asyncio.run(rebase_v3._v3_publish(env.ctx))
    assert not result.ok and "hooks changed validated content" in result.summary
    assert git(env.remote, "for-each-ref") == ""


def test_unchanged_staging_survives_a_failed_commit(publication):
    env = publication
    hook = env.repo / ".git/hooks/pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    result = asyncio.run(rebase_v3._v3_publish(env.ctx))
    assert not result.ok and "local commit failed" in result.summary
    assert git(env.repo, "diff", "--cached", "--name-only") == "module.py"
    hook.unlink()
    result = asyncio.run(rebase_v3._v3_publish(env.ctx))
    assert result.ok, result.summary
    assert git(env.remote, "rev-parse", "refs/heads/codex/afd-sync") == git(
        env.repo, "rev-parse", "HEAD")


def test_diverged_remote_is_preserved_on_first_push_and_resume(publication, monkeypatch):
    env = publication
    other = env.run.parent / "other-contributor"
    subprocess.run(["git", "clone", "-q", str(env.repo), str(other)],
                   capture_output=True, check=True)
    git(other, "config", "user.name", "Other contributor")
    git(other, "config", "user.email", "other@example.invalid")
    (other / "remote_only.py").write_text("remote_change = 1\n")
    git(other, "add", ".")
    git(other, "commit", "-qm", "other contributor's change")
    remote_tip = git(other, "rev-parse", "HEAD")
    git(other, "push", str(env.remote), "HEAD:refs/heads/codex/afd-sync")
    real_push = push_to_ci.commit_and_push

    def bounded_push(*args, **kwargs):
        return real_push(*args, **kwargs, push_retries=1, push_base_delay=0)

    monkeypatch.setattr(push_to_ci, "commit_and_push", bounded_push)
    for attempt in range(2):
        result = asyncio.run(rebase_v3._v3_publish(env.ctx))
        assert not result.ok, f"attempt {attempt + 1} overwrote diverged remote"
        assert git(env.remote, "rev-parse", "refs/heads/codex/afd-sync") == remote_tip
    assert git(env.repo, "status", "--porcelain") == ""


def test_uv_lock_checks_resolved_and_project_metadata(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="plugin"\n[project.optional-dependencies]\n'
        'runtime=["runtime-package==1.2.0"]\n')
    lock = tmp_path / "uv.lock"
    template = ('[[package]]\nname="runtime-package"\nversion="{version}"\n'
                '[[package]]\nname="plugin"\n'
                '[[package.metadata.requires-dist]]\nname="runtime-package"\n'
                'specifier="=={metadata}"\n')
    for version, metadata in [("1.1.0", "1.1.0"), ("1.2.0", "1.1.0")]:
        lock.write_text(template.format(version=version, metadata=metadata))
        assert check_uv_dependency(tmp_path, package="runtime-package", extra="runtime",
                                   version="1.2.0")
    lock.write_text(template.format(version="1.2.0", metadata="1.2.0"))
    assert check_uv_dependency(tmp_path, package="runtime-package", extra="runtime",
                               version="1.2.0") == ""
