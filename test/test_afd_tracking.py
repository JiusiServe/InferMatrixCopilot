"""Rolling AFD maintenance over local Git histories; no model or network calls."""

import asyncio
from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest

from infermatrix_copilot.engine.steps import rebase_v3
from infermatrix_copilot.engine.step import StepContext
from infermatrix_copilot.rebase_engine import pytest_results, wheel
from infermatrix_copilot.rebase_engine.prompt_builder import ModulePromptData, build_module_prompt
from infermatrix_copilot.rebase_engine import upstream_tracking as tracking
from infermatrix_copilot.rebase_engine.dependency_lock import check_uv_dependency
from infermatrix_copilot.rebase_engine.substate import Substate
from infermatrix_copilot.rebase_engine.wheel import WheelPickError, WheelSpec
from test_afd_sync_state import ROOT, clone, commit, git, init_repo


pytest_plugins = ("test_afd_publish", "test_afd_sync_state")


SPEC = WheelSpec("vllm", "https://wheels.example/{commit}/{variant}/{package}/",
                 "cu130", "x86_64")


@pytest.fixture
def upstream(tmp_path, monkeypatch):
    remote = init_repo(tmp_path / "remote")
    first = commit(remote, {"module.py": "value = 1\n"}, "baseline")
    canonical = clone(remote, tmp_path / "canonical")
    scratch = clone(canonical, tmp_path / "scratch")
    available = {first}
    monkeypatch.setattr(tracking, "make_arch_probe", lambda spec: available.__contains__)

    def select(run="run", baseline=first):
        return tracking.select_target(
            scratch, canonical, remote="origin", branch="main", baseline=baseline,
            spec=SPEC, sub=Substate(tmp_path / run, run))

    return SimpleNamespace(remote=remote, canonical=canonical, scratch=scratch,
                           first=first, available=available, select=select,
                           root=tmp_path)


def test_selects_latest_wheel_from_remote_not_stale_canonical_and_freezes(upstream):
    env = upstream
    second = commit(env.remote, {"module.py": "value = 2\n"}, "wheel ready")
    env.available.add(second)
    commit(env.remote, {"module.py": "value = 3\n"}, "no wheel yet")
    selected = env.select()
    assert selected["selected_sha"] == second
    assert git(env.canonical, "rev-parse", "HEAD") == env.first
    fourth = commit(env.remote, {"module.py": "value = 4\n"}, "next run")
    env.available.add(fourth)
    assert env.select()["selected_sha"] == second
    assert env.select("next", second)["selected_sha"] == fourth


def test_no_new_wheel_keeps_baseline_without_rolling_back(upstream):
    env = upstream
    second = commit(env.remote, {"module.py": "value = 2\n"}, "last successful")
    env.available.add(second)
    commit(env.remote, {"module.py": "value = 3\n"}, "pending wheel")
    assert env.select(baseline=second)["selected_sha"] == second
    env.available.remove(second)
    with pytest.raises(WheelPickError, match="at or after"):
        env.select("missing", second)


def test_failed_selection_retries_frozen_main_snapshot(upstream):
    env = upstream
    second = commit(env.remote, {"module.py": "value = 2\n"}, "pending")
    env.available.clear()
    with pytest.raises(WheelPickError):
        env.select()
    third = commit(env.remote, {"module.py": "value = 3\n"}, "later main")
    env.available.update({second, third})
    assert env.select()["selected_sha"] == second


def test_probe_work_is_bounded_and_never_rewinds(upstream, monkeypatch):
    env = upstream
    monkeypatch.setattr(tracking, "MAX_WHEEL_PROBES", 2)
    for number in range(3):
        commit(env.remote, {"module.py": f"value = {number + 2}\n"}, "no wheel")
    with pytest.raises(WheelPickError, match="within 2"):
        env.select()
    assert "selected_sha" not in Substate(env.root / "run", "run").get("upstream_tracking")


def test_unrelated_baseline_is_rejected(upstream):
    env = upstream
    other = commit(env.canonical, {"unrelated.py": "True\n"}, "not upstream")
    git(env.scratch, "fetch", "origin")
    with pytest.raises(WheelPickError):
        env.select(baseline=other)


def test_resume_rejects_changed_wheel_configuration(upstream):
    env = upstream
    env.select()
    with pytest.raises(WheelPickError, match="configuration changed"):
        tracking.select_target(
            env.scratch, env.canonical, remote="origin", branch="main",
            baseline=env.first, spec=WheelSpec("vllm", SPEC.index_url_template,
                                            "cu999", "x86_64"),
            sub=Substate(env.root / "run", "run"))


def test_sync_recovers_published_baseline_and_ignores_unpushed_progress(sync_env):
    env = sync_env
    env.manifest["upstream"] = {"tracking": "latest_wheel"}
    branch = env.manifest["push"]["rebase_branch"]
    git(env.fork, "checkout", "-qb", branch)
    commit(env.fork, {"adapted.py": "True"},
           f"adapted\n\n{tracking.UPSTREAM_TRAILER}: {'a' * 40}")
    first = asyncio.run(rebase_v3._v3_sync_target(env.context()))
    assert first.ok, first.summary
    assert first.outputs["state_updates"]["last_rebase_upstream_commit"] == "a" * 40
    commit(env.repo, {"not_published.py": "True"},
           f"local only\n\n{tracking.UPSTREAM_TRAILER}: {'b' * 40}")
    again = asyncio.run(rebase_v3._v3_sync_target(env.context("next")))
    assert again.ok, again.summary
    assert again.outputs["state_updates"]["last_rebase_upstream_commit"] == "a" * 40


def test_first_tracking_run_requires_explicit_baseline_before_merge(sync_env):
    env = sync_env
    env.manifest["upstream"] = {"tracking": "latest_wheel"}
    head = git(env.repo, "rev-parse", "HEAD")
    ctx = env.context()
    result = asyncio.run(rebase_v3._v3_sync_target(ctx))
    assert not result.ok and "first tracking run" in result.summary
    assert git(env.repo, "rev-parse", "HEAD") == head
    ctx.state["task_spec"]["params"]["last_rebase_commit"] = "a" * 40
    result = asyncio.run(rebase_v3._v3_sync_target(ctx))
    assert result.ok, result.summary
    assert result.outputs["state_updates"]["last_rebase_upstream_commit"] == "a" * 40


def test_disabled_push_does_not_publish_success_baseline(publication):
    env = publication
    env.manifest["upstream"] = {"tracking": "latest_wheel"}
    env.ctx.settings.allow_push = False
    result = asyncio.run(rebase_v3._v3_publish(env.ctx))
    assert not result.ok
    assert tracking.published_baseline(env.repo, "HEAD") == "a" * 40
    assert not git(env.remote, "for-each-ref")
    env.ctx.settings.allow_push = True
    result = asyncio.run(rebase_v3._v3_publish(env.ctx))
    assert result.ok, result.summary
    assert tracking.published_baseline(env.remote, "refs/heads/codex/afd-sync") == "a" * 40


def test_successful_target_without_code_changes_is_recorded_once(publication):
    env = publication
    env.manifest["upstream"] = {"tracking": "latest_wheel"}
    git(env.repo, "restore", "module.py")
    env.ctx.state["afd_validation_worktree_digest"] = rebase_v3._worktree_digest(env.repo)
    old_head = git(env.repo, "rev-parse", "HEAD")
    result = asyncio.run(rebase_v3._v3_publish(env.ctx))
    assert result.ok, result.summary
    new_head = git(env.repo, "rev-parse", "HEAD")
    assert new_head != old_head
    assert git(env.repo, "rev-parse", "HEAD^{tree}") == git(env.repo, "rev-parse", old_head + "^{tree}")
    assert tracking.published_baseline(env.remote, "refs/heads/codex/afd-sync") == "a" * 40
    result = asyncio.run(rebase_v3._v3_publish(env.ctx))
    assert result.ok, result.summary
    assert git(env.repo, "rev-parse", "HEAD") == new_head


def test_nightly_lock_requires_selected_commit_index(tmp_path):
    version = "0.29.0.dev123"
    index = "https://wheels.example/" + "a" * 40 + "/cu130/"
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="afd"\n[project.optional-dependencies]\n'
        f'vllm=["vllm=={version}"]\n[tool.uv.sources]\n'
        'vllm={index="vllm-upstream"}\n[[tool.uv.index]]\n'
        f'name="vllm-upstream"\nurl="{index}"\nexplicit=true\n')
    lock = ('[[package]]\nname="vllm"\n'
            f'version="{version}+gabcdef.cu130"\n'
            'source={registry="INDEX"}\n[[package]]\nname="afd"\n'
            '[[package.metadata.requires-dist]]\nname="vllm"\n'
            f'specifier="=={version}"\nindex="{index}"\n')
    (tmp_path / "uv.lock").write_text(lock.replace("INDEX", index))
    assert not check_uv_dependency(tmp_path, package="vllm", extra="vllm",
                                   version=version, index_url=index)
    (tmp_path / "uv.lock").write_text(lock.replace("INDEX", "https://pypi.org/simple/"))
    assert "different commit" in check_uv_dependency(
        tmp_path, package="vllm", extra="vllm", version=version, index_url=index)
    (tmp_path / "uv.lock").write_text(lock.replace("INDEX", index).replace(
        f'index="{index}"', 'index="https://old.example/"'))
    assert "metadata is stale" in check_uv_dependency(
        tmp_path, package="vllm", extra="vllm", version=version, index_url=index)


def test_wheel_step_resumes_selected_commit_and_uses_its_runtime_version(upstream, monkeypatch):
    env = upstream
    selected = commit(env.remote, {"module.py": "value = 2\n"}, "wheel ready")
    env.available.add(selected)
    repo = init_repo(env.root / "afd")
    commit(repo, {"module.py": "True\n"}, "afd")
    manifest = {"upstream": {"tracking": "latest_wheel", "target_branch": "main"},
                "repo": {"venv": str(env.root / "venv")},
                "rebase": {"wheel": asdict(SPEC),
                           "test_manifest": {"yaml_dir": ".ci", "pipelines": {}}}}
    monkeypatch.setattr(rebase_v3, "_adapter_manifest", lambda ctx: manifest)
    monkeypatch.setattr(rebase_v3, "_ensure_checkout_locks", lambda *args: None)
    monkeypatch.setattr(rebase_v3, "_ensure_upstream_scratch", lambda ctx: str(env.scratch))
    monkeypatch.setattr(rebase_v3, "_target_test_env", lambda *args: {})
    ctx = StepContext(
        settings=SimpleNamespace(expansion_env=lambda: {}),
        state={"repo_path": str(repo), "upstream_origin_path": str(env.canonical),
               "last_rebase_upstream_commit": env.first,
               "task_spec": {"params": {"rebase_mode": "local_rebase"}}},
        params={}, run_dir=env.root / "wheel-run",
        trace=SimpleNamespace(record=lambda *args, **kwargs: None))
    calls = []

    def install(path, sha, spec, **kwargs):
        calls.append(sha)
        assert spec.install_env["VLLM_PRECOMPILED_WHEEL_COMMIT"] == selected
        assert spec.install_env["VLLM_PRECOMPILED_WHEEL_VARIANT"] == "cu130"
        if len(calls) == 1:
            raise wheel.WheelInstallError("transient download failure")
        return True

    monkeypatch.setattr(wheel, "ensure_wheel_installed", install)
    monkeypatch.setattr(wheel, "read_installed_version",
                        lambda *args, **kwargs: "0.29.0.dev7+g" + selected[:8] + ".precompiled")
    identities = []
    monkeypatch.setattr(pytest_results, "runtime_identity",
                        lambda *args, **kwargs: identities.append((args, kwargs)) or {})
    first = asyncio.run(rebase_v3._v3_wheel(ctx))
    assert not first.ok and "download failure" in first.summary
    later = commit(env.remote, {"module.py": "value = 3\n"}, "next run")
    env.available.add(later)
    resumed = asyncio.run(rebase_v3._v3_wheel(ctx))
    assert resumed.ok, resumed.summary
    assert calls == [selected, selected]
    assert identities[0][0][2] == "0.29.0.dev7"
    assert identities[0][1]["commit"] == selected
    assert resumed.outputs["state_updates"]["vllm_target_version"] == "0.29.0.dev7"


def test_module_prompt_carries_dynamic_dependency_contract():
    target = {"main_sha": "a" * 40, "selected_sha": "b" * 40,
              "version": "0.29.0.dev7", "index_url": "https://wheels.example/commit/cu130/"}
    data = replace(ModulePromptData.load(ROOT / "adapters/afd_plugin/rebase"),
                   runtime_contract=tracking.runtime_contract(target))
    prompt = build_module_prompt(
        "plugin_boundary", data, vllm_path="/upstream", omni_path="/afd",
        script_dir="/scripts", run_git=lambda *args: "fixture")
    assert "vllm==0.29.0.dev7" in prompt
    assert target["index_url"] in prompt and "regenerate uv.lock" in prompt


def test_report_only_selects_available_wheel_without_moving_canonical(upstream, monkeypatch):
    env = upstream
    selected = commit(env.remote, {"module.py": "value = 2\n"}, "ready")
    env.available.add(selected)
    commit(env.remote, {"module.py": "value = 3\n"}, "pending wheel")
    manifest = {"repo": {}, "modules": {"boundary": {"upstream_paths": ["module.py"]}},
                "upstream": {"tracking": "latest_wheel", "target_branch": "main",
                             "repo_path": str(env.canonical)},
                "rebase": {"wheel": asdict(SPEC),
                           "test_manifest": {"yaml_dir": ".ci", "pipelines": {}}}}
    monkeypatch.setattr(rebase_v3, "_adapter_manifest", lambda ctx: manifest)
    monkeypatch.setattr(rebase_v3, "_ensure_upstream_scratch", lambda ctx: str(env.scratch))
    run = env.root / "preview"
    run.mkdir()
    ctx = StepContext(
        settings=SimpleNamespace(expansion_env=lambda: {}),
        state={"repo_path": str(env.canonical), "task_spec": {
            "params": {"rebase_mode": "report_only", "last_rebase_commit": env.first}}},
        params={}, run_dir=run, trace=SimpleNamespace(record=lambda *args, **kwargs: None))
    result = asyncio.run(rebase_v3._v3_scan(ctx))
    assert result.ok, result.summary
    assert result.outputs["state_updates"]["upstream_assignment"]["head"] == selected
    assert git(env.canonical, "rev-parse", "HEAD") == env.first
