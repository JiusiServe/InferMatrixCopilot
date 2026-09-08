"""Local Git regressions for fixed inputs, target sync, and rebase resume."""

from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.engine.agent_runtime import runner as agent_runner
from infermatrix_copilot.engine import lifecycle
from infermatrix_copilot.engine.executor import RunOutcome
from infermatrix_copilot.engine.step import FailureKind, StepContext, StepResult
from infermatrix_copilot.engine.steps import rebase_v3
from infermatrix_copilot.engine.steps.rebase_v3 import _register_scratch_teardown
from infermatrix_copilot.rebase_engine.substate import Substate

ROOT = Path(__file__).resolve().parents[1]
RESULT_BRANCH = "codex/vllm-0.28-sync"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True,
        text=True, check=True).stdout.strip()


def init_repo(path: Path) -> Path:
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.name", "fixture")
    git(path, "config", "user.email", "fixture@example.invalid")
    return path


def commit(repo: Path, files: dict[str, str], message: str) -> str:
    for rel, body in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", message)
    return git(repo, "rev-parse", "HEAD")


def clone(source: Path, target: Path) -> Path:
    subprocess.run(["git", "clone", "-q", str(source), str(target)],
                   capture_output=True, check=True)
    git(target, "config", "user.name", "fixture")
    git(target, "config", "user.email", "fixture@example.invalid")
    return target


@pytest.fixture
def sync_env(tmp_path, monkeypatch):
    source = init_repo(tmp_path / "source")
    base = commit(source, {"afd_plugin/config.py": "API = 26\n",
                           "afd_plugin/runtime.py": "RUNTIME = 26\n"}, "main")
    fork = clone(source, tmp_path / "fork")
    repo = clone(source, tmp_path / "isolated")
    git(repo, "remote", "rename", "origin", "upstream")
    git(repo, "remote", "add", "fork", str(fork))
    manifest = {
        "repo": {"source_remote": "upstream", "default_branch": "main"},
        "push": {"default_remote": "fork", "rebase_branch": RESULT_BRANCH},
        "modules": {
            "boundary": {"local_paths": ["afd_plugin/config.py"]},
            "runtime": {"local_paths": ["afd_plugin/runtime.py"]},
        },
    }
    monkeypatch.setattr(rebase_v3, "_adapter_manifest", lambda ctx: manifest)
    monkeypatch.setattr(rebase_v3, "_ensure_checkout_locks", lambda *args: None)
    monkeypatch.setattr(rebase_v3, "_register_scratch_teardown", lambda *args: None)

    def context(name="run"):
        run_dir = tmp_path / name
        run_dir.mkdir()
        return StepContext(
            settings=SimpleNamespace(max_agent_iters=3, expansion_env=lambda: {}),
            state={"repo_path": str(repo), "task_spec": {
                "repo": "afd_plugin", "params": {"rebase_mode": "local_rebase"}}},
            params={}, run_dir=run_dir,
            trace=SimpleNamespace(record=lambda *args, **kwargs: None))

    return SimpleNamespace(source=source, fork=fork, repo=repo, base=base,
                           manifest=manifest, context=context)


def test_sync_inherits_remote_branch_and_only_assigns_incoming_main(sync_env):
    env = sync_env
    git(env.fork, "checkout", "-qb", RESULT_BRANCH)
    adapted = commit(env.fork, {"afd_plugin/config.py": "API = 28\n"}, "adapt")
    main = commit(env.source, {"afd_plugin/runtime.py": "RUNTIME = 27\n"}, "new main")
    ctx = env.context()
    result = asyncio.run(rebase_v3._v3_sync_target(ctx))
    assert result.ok, result.summary
    state = result.outputs["state_updates"]
    assert state["afd_branch_start_sha"] == adapted
    assert state["afd_main_sha"] == main
    assert git(env.repo, "show", "HEAD:afd_plugin/config.py") == "API = 28"
    git(env.repo, "merge-base", "--is-ancestor", adapted, "HEAD")
    git(env.repo, "merge-base", "--is-ancestor", main, "HEAD")
    changes = rebase_v3._classify_target_main_changes(
        str(env.repo), state["afd_main_base_sha"], state["afd_main_sha"],
        env.manifest["modules"])
    assert changes["affected_modules"] == ["runtime"]


def test_sync_new_branch_uses_main_and_does_not_modify_unrelated_branch(sync_env):
    env = sync_env
    unrelated = commit(env.repo, {"personal.txt": "unrelated"}, "personal branch")
    result = asyncio.run(rebase_v3._v3_sync_target(env.context()))
    assert result.ok, result.summary
    assert result.outputs["state_updates"]["afd_branch_start_sha"] == env.base
    assert git(env.repo, "rev-parse", "main") == unrelated
    assert not (env.repo / "personal.txt").exists()


def test_sync_requires_adapter_opt_in(sync_env, monkeypatch):
    env = sync_env
    env.manifest["repo"].pop("source_remote")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("unexpected git"))
    result = asyncio.run(rebase_v3._v3_sync_target(env.context()))
    assert result.ok and "does not request" in result.summary


def test_sync_refuses_diverged_result_histories(sync_env):
    env = sync_env
    git(env.fork, "checkout", "-qb", RESULT_BRANCH)
    remote = commit(env.fork, {"remote.txt": "remote"}, "remote adaptation")
    git(env.repo, "checkout", "-qb", RESULT_BRANCH)
    local = commit(env.repo, {"local.txt": "local"}, "local adaptation")
    result = asyncio.run(rebase_v3._v3_sync_target(env.context()))
    assert not result.ok and "diverged" in result.summary
    assert git(env.repo, "rev-parse", "HEAD") == local
    assert git(env.fork, "rev-parse", RESULT_BRANCH) == remote


def test_same_run_keeps_inputs_and_new_run_discovers_new_main(sync_env):
    env = sync_env
    git(env.fork, "checkout", "-qb", RESULT_BRANCH)
    commit(env.fork, {"afd_plugin/config.py": "API = 28\n"}, "adapt")
    ctx = env.context()
    result = asyncio.run(rebase_v3._v3_sync_target(ctx))
    assert result.ok, result.summary
    state = result.outputs["state_updates"]
    unchanged = rebase_v3._classify_target_main_changes(
        str(env.repo), state["afd_main_base_sha"], state["afd_main_sha"],
        env.manifest["modules"])
    assert unchanged["changed_paths"] == []
    Substate(ctx.run_dir, ctx.run_dir.name).update({"modules": {"runtime": {"status": "done"}}})
    updated = commit(env.source, {"afd_plugin/runtime.py": "RUNTIME = 27\n"}, "later main")
    resumed = asyncio.run(rebase_v3._v3_sync_target(ctx))
    assert resumed.ok and resumed.outputs["state_updates"]["afd_main_sha"] == env.base
    fresh = env.context("next-run")
    next_result = asyncio.run(rebase_v3._v3_sync_target(fresh))
    assert next_result.ok, next_result.summary
    assert next_result.outputs["state_updates"]["afd_main_sha"] == updated
    assert "modules" not in Substate(fresh.run_dir, fresh.run_dir.name).read()


@pytest.mark.parametrize("first_failure", ["interrupted", "failed"])
def test_conflict_resume_preserves_partial_resolution_and_fixed_main(
        sync_env, monkeypatch, first_failure):
    env = sync_env
    git(env.fork, "checkout", "-qb", RESULT_BRANCH)
    commit(env.fork, {"afd_plugin/config.py": "API = 28\n",
                      "afd_plugin/runtime.py": "RUNTIME = 28\n"}, "adapt")
    main = commit(env.source, {"afd_plugin/config.py": "API = 27\n",
                               "afd_plugin/runtime.py": "RUNTIME = 27\n"}, "main changes")
    ctx = env.context()

    async def partial(*args, **kwargs):
        (env.repo / "afd_plugin/config.py").write_text("API = (27, 28)\n")
        git(env.repo, "add", "afd_plugin/config.py")
        if first_failure == "interrupted":
            raise RuntimeError("process interrupted")
        return StepResult(False, FailureKind.BLOCKED, "budget exhausted"), {}

    monkeypatch.setattr(agent_runner, "run_agent_step", partial)
    if first_failure == "interrupted":
        with pytest.raises(RuntimeError, match="interrupted"):
            asyncio.run(rebase_v3._v3_sync_target(ctx))
    else:
        result = asyncio.run(rebase_v3._v3_sync_target(ctx))
        assert not result.ok and "preserved" in result.summary
    assert git(env.repo, "rev-parse", "MERGE_HEAD") == main
    later = commit(env.source, {"later.txt": "next run only"}, "later main")

    async def finish(*args, **kwargs):
        assert (env.repo / "afd_plugin/config.py").read_text() == "API = (27, 28)\n"
        assert kwargs["evidence"]["source_sha"] == main
        (env.repo / "afd_plugin/runtime.py").write_text("RUNTIME = (27, 28)\n")
        git(env.repo, "add", "afd_plugin/runtime.py")
        return StepResult(True), {}

    monkeypatch.setattr(agent_runner, "run_agent_step", finish)
    result = asyncio.run(rebase_v3._v3_sync_target(ctx))
    assert result.ok, result.summary
    assert result.outputs["state_updates"]["afd_main_sha"] == main != later
    assert not (env.repo / "later.txt").exists()
    assert git(env.repo, "status", "--porcelain") == ""


def test_scratch_recreation_restores_target_and_keeps_surviving_edits(sync_env):
    env = sync_env
    target = env.base
    commit(env.source, {"newer.txt": "beyond target"}, "newer canonical HEAD")
    ctx = env.context()
    ctx.state.update(upstream_origin_path=str(env.source), vllm_target_sha=target)
    scratch = Path(rebase_v3._ensure_upstream_scratch(ctx))
    assert git(scratch, "rev-parse", "HEAD") == target
    (scratch / "afd_plugin/config.py").write_text("temporary analysis edit\n")
    assert rebase_v3._ensure_upstream_scratch(ctx) == str(scratch)
    assert (scratch / "afd_plugin/config.py").read_text() == "temporary analysis edit\n"
    shutil.rmtree(scratch)
    restored = rebase_v3._ensure_upstream_scratch(ctx)
    assert git(Path(restored), "rev-parse", "HEAD") == target
    assert not (Path(restored) / "newer.txt").exists()


def test_scratch_missing_fixed_target_blocks_instead_of_adopting_head(sync_env):
    env = sync_env
    ctx = env.context()
    ctx.state.update(upstream_origin_path=str(env.source), vllm_target_sha="f" * 40)
    result = rebase_v3._ensure_upstream_scratch(ctx)
    assert isinstance(result, StepResult) and not result.ok
    again = rebase_v3._ensure_upstream_scratch(ctx)
    assert isinstance(again, StepResult) and not again.ok


@pytest.mark.parametrize("mode,status,preserve", [
    ("local_rebase", "blocked", True),
    ("local_rebase", "failed", True),
    ("local_rebase", "done", False),
    ("local_rebase", None, False),
    ("full", "blocked", False),
])
def test_failed_local_run_keeps_editable_runtime_for_resume(
        sync_env, monkeypatch, mode, status, preserve):
    env = sync_env
    monkeypatch.setattr(rebase_v3, "_register_scratch_teardown",
                        _register_scratch_teardown)
    ctx = env.context()
    ctx.state["task_spec"]["params"]["rebase_mode"] = mode
    ctx.state.update(upstream_origin_path=str(env.source), vllm_target_sha=env.base)
    scratch = Path(rebase_v3._ensure_upstream_scratch(ctx))
    artifact = scratch / "native-artifact.so"
    artifact.write_bytes(b"run-owned native artifact")

    async def stopped():
        return RunOutcome(status=status)

    if status is None:
        asyncio.run(lifecycle.finalize(ctx.run_dir, None))
    else:
        outcome = asyncio.run(lifecycle.run_guarded(stopped(), ctx.run_dir))
        assert outcome.status == status
    assert scratch.exists() == preserve
    if preserve:
        commit(env.source, {"later.txt": "later upstream"}, "canonical advanced")
        resumed = Path(rebase_v3._ensure_upstream_scratch(ctx))
        assert git(resumed, "rev-parse", "HEAD") == env.base
        assert artifact.read_bytes() == b"run-owned native artifact"
        asyncio.run(lifecycle.finalize(ctx.run_dir, RunOutcome(status="done")))
        assert not scratch.exists()


def test_report_only_uses_target_tag_without_changing_checkout(sync_env):
    env = sync_env
    baseline = commit(env.source, {"vllm/config.py": "BASE = 1\n"}, "old upstream")
    target = commit(env.source, {"vllm/config.py": "BASE = 2\n"}, "release")
    git(env.source, "tag", "v0.28.0", target)
    head = commit(env.source, {"vllm/config.py": "BASE = 3\n"}, "later upstream")
    env.manifest.update(yaml.safe_load((ROOT / "adapters/afd_plugin/manifest.yaml").read_text()))
    env.manifest["upstream"]["repo_path"] = str(env.source)
    env.manifest["modules"] = {"boundary": {"upstream_paths": ["vllm/config.py"]}}
    ctx = env.context()
    ctx.state["task_spec"]["params"].update(last_rebase_commit=baseline)
    result = asyncio.run(rebase_v3._v3_scan(ctx))
    assert result.ok, result.summary
    assignment = result.outputs["state_updates"]["upstream_assignment"]
    assert assignment["head"] == target and assignment["total_commits"] == 1
    assert git(env.source, "rev-parse", "HEAD") == head
    env.manifest["upstream"]["target_ref"] = "v0.28-missing"
    missing = asyncio.run(rebase_v3._v3_scan(ctx))
    assert not missing.ok and "v0.28-missing" in missing.summary


@pytest.mark.parametrize("change", ["delete", "rename"])
def test_assignment_keeps_deleted_or_renamed_upstream_paths(sync_env, change):
    env = sync_env
    baseline = commit(env.source, {"vllm/sequence.py": "class Sequence: pass\n",
                                    "vllm/config.py": "CONFIG = 1\n"}, "old API")
    if change == "delete":
        git(env.source, "rm", "vllm/sequence.py")
    else:
        git(env.source, "mv", "vllm/sequence.py", "vllm/new_sequence.py")
    git(env.source, "commit", "-qm", "remove old API path")
    env.manifest["modules"] = {"runtime": {
        "upstream_paths": ["vllm/config.py", "vllm/sequence.py"], "wave": 1}}
    ctx = env.context()
    ctx.state.update(upstream_origin_path=str(env.source),
                     last_rebase_upstream_commit=baseline,
                     vllm_target_sha=git(env.source, "rev-parse", "HEAD"))
    result = asyncio.run(rebase_v3._v3_assign(ctx))
    assert result.ok, result.summary
    assert result.outputs["state_updates"]["active_modules"] == ["runtime"]
    assert "vllm/sequence.py" in (ctx.run_dir / "path_drift_check.md").read_text()
