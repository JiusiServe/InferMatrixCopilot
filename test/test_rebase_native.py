"""Stage 2: native decomposition playbook wrapping the parent agent's functions."""

import asyncio
import json

import pytest

from omni_copilot.config import _REPO_ROOT
from omni_copilot.engine import Executor, StepRegistry
from omni_copilot.engine.builtin_steps import register_builtin_steps
from omni_copilot.engine import rebase_native_steps as rns
from omni_copilot.notify import Notifier
from omni_copilot.playbooks.store import PlaybookStore


@pytest.fixture()
def native_env(settings, trace, tmp_path, fake_agent, git_repo):
    registry = register_builtin_steps(StepRegistry())
    store = PlaybookStore(_REPO_ROOT / "playbooks", registry)
    playbook = store.get("repo-rebase-native")
    assert playbook is not None and playbook.status == "candidate"
    run_dir = tmp_path / "copilot_run"
    notifier = Notifier(settings, run_dir, trace, "run-native")
    executor = Executor(registry, settings, run_dir=run_dir, trace=trace,
                        notifier=notifier)
    settings.allow_push = True  # let the fake phase4 run in the happy path
    state = {"task_spec": {"kind": "repo_rebase", "params": {}},
             "repo_path": str(git_repo)}
    return executor, playbook, state, notifier


def test_native_happy_path(native_env, fake_agent, trace):
    executor, playbook, state, _ = native_env
    outcome = asyncio.run(executor.run(playbook, state))
    assert outcome.status == "done", outcome.blocked_reason

    # all wave-1 modules then wave-2 went through the parent's node_rebase_module
    assert fake_agent["module_calls"] == ["m1", "m2", "m3"]
    # parent phase wrappers were invoked in order
    assert fake_agent["phase_calls"] == ["phase1", "phase3", "phase4", "phase5"]
    # parent phase markers written in the parent's own order (parent --resume viable)
    assert fake_agent["persisted_markers"] == [
        "module_rebase", "module_rebase", "local_testing", "ci_e2e", "done"]
    # stores initialized, curators ran, env exported + audited
    assert fake_agent["stores"] == ["dm", "skills"]
    assert fake_agent.get("preflight") and fake_agent.get("postrun")
    assert list(trace.events("env_exported"))
    # per-module progress persisted into the parent's state.json
    parent = json.loads(fake_agent["state_file"].read_text())
    assert parent["phase2_progress"]["modules"]["m3"]["status"] == "done"


def test_wave1_failure_gates_wave2(native_env, fake_agent, tmp_path):
    executor, playbook, state, notifier = native_env
    fake_agent["module_results"]["m2"] = {"status": "failed", "exit_code": 1,
                                          "debug_attempts": 3}
    outcome = asyncio.run(executor.run(playbook, state))
    assert outcome.status == "blocked"
    assert "m3" not in fake_agent["module_calls"]          # wave 2 never ran
    assert fake_agent["phase_calls"] == ["phase1"]          # phase 3+ never ran
    assert notifier.sent and notifier.sent[0].state_summary.get("module") == "m2"


def test_transient_module_error_retried_once(native_env, fake_agent):
    executor, playbook, state, _ = native_env
    calls = {"n": 0}
    orig = fake_agent["module_results"]

    # first m1 call: pre-agent exception shape; then clean
    async def scripted(st):
        module = st.get("module")
        fake_agent["module_calls"].append(module)
        if module == "m1" and calls["n"] == 0:
            calls["n"] += 1
            return {"modules": {"m1": {"status": "failed", "exit_code": -1,
                                       "debug_attempts": 0}}}
        return {"modules": {module: {"status": "done", "exit_code": 0,
                                     "debug_attempts": 0}}}
    import sys
    sys.modules["agent.nodes.phase2_rebase"].node_rebase_module = scripted

    outcome = asyncio.run(executor.run(playbook, state))
    assert outcome.status == "done"
    assert fake_agent["module_calls"].count("m1") == 2      # retried exactly once


def test_prelude_refuses_inflight_state(native_env, fake_agent):
    executor, playbook, state, _ = native_env
    fake_agent["state_file"].write_text(json.dumps(
        {"run_id": "rebase-other", "phase": "module_rebase"}))
    state["task_spec"]["params"] = {}
    # point the prelude's in-flight check at the fake state file
    playbook.steps[1].params = {"state_file": str(fake_agent["state_file"])}
    outcome = asyncio.run(executor.run(playbook, state))
    assert outcome.status == "blocked"
    assert "in-flight run" in outcome.blocked_reason
    playbook.steps[1].params = {}


def test_resume_skips_done_modules_in_new_process(native_env, fake_agent, tmp_path):
    executor, playbook, state, _ = native_env
    # previous run: m1 done, crashed during m2; parent state.json reflects it
    fake_agent["state_file"].write_text(json.dumps({
        "run_id": "rebase-test-0001", "phase": "module_rebase",
        "phase2_progress": {"run_id": "rebase-test-0001", "modules": {
            "m1": {"status": "done", "exit_code": 0}}},
    }))
    # copilot progress: guard+prelude+phase1+p2prep completed with the wave lists
    executor.run_dir.mkdir(parents=True, exist_ok=True)
    executor.progress_file.write_text(json.dumps({"completed": {
        "guard": {"summary": "clean", "outputs": {}},
        "prelude": {"summary": "ready", "outputs": {"state_updates": {
            "wave1_modules": ["m1", "m2"], "wave2_modules": ["m3"],
            "rebase_run_id": "rebase-test-0001",
            "parent_log_dir": str(tmp_path / "agent_root" / "logs")}}},
        "phase1": {"summary": "done", "outputs": {}},
        "p2prep": {"summary": "done", "outputs": {}},
    }}))
    rns._RUNTIME.clear()  # simulate a fresh process
    state["resuming"] = True
    outcome = asyncio.run(executor.run(playbook, state))
    assert outcome.status == "done", outcome.blocked_reason
    # m1 was NOT re-run (resume granularity honored); m2, m3 ran
    assert "m1" not in fake_agent["module_calls"]
    assert fake_agent["module_calls"] == ["m2", "m3"]


def test_continue_on_module_failure_parity_mode(native_env, fake_agent):
    executor, playbook, state, _ = native_env
    fake_agent["module_results"]["m1"] = {"status": "failed", "exit_code": 1,
                                          "debug_attempts": 3}
    for step in playbook.steps:
        if step.step == "rebase.module_rebase":
            step.params = {"continue_on_module_failure": True}
    outcome = asyncio.run(executor.run(playbook, state))
    for step in playbook.steps:
        if step.step == "rebase.module_rebase":
            step.params = {}
    assert outcome.status == "done"                         # lenient parent semantics
    assert fake_agent["module_calls"] == ["m1", "m2", "m3"]


def test_phase4_forbidden_without_allow_push(native_env, fake_agent, settings):
    executor, playbook, state, _ = native_env
    settings.allow_push = False
    outcome = asyncio.run(executor.run(playbook, state))
    assert outcome.status == "blocked"
    assert "ALLOW_PUSH=0" in outcome.blocked_reason
    assert "phase4" not in fake_agent["phase_calls"]        # parent never pushed


def test_native_blocked_without_parent_package(settings, trace, tmp_path, git_repo,
                                               monkeypatch):
    import builtins
    real_import = builtins.__import__

    def no_agent(name, *args, **kwargs):
        if name == "agent" or name.startswith("agent."):
            raise ImportError("agent not installed")
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", no_agent)
    rns._RUNTIME.clear()

    registry = register_builtin_steps(StepRegistry())
    from omni_copilot.engine.step import StepContext
    ctx = StepContext(settings=settings, state={"task_spec": {}}, params={},
                      run_dir=tmp_path, trace=trace)
    result = asyncio.run(registry.get("rebase.prelude").handler(ctx))
    assert not result.ok and result.failure.value == "blocked"
    assert "not importable" in result.summary
