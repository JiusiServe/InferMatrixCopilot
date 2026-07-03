import subprocess
from pathlib import Path

import pytest

from omni_copilot.config import Settings
from omni_copilot.run_trace import RunTrace


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        run_root=tmp_path / "runs",
        playbooks_dir=tmp_path / "playbooks",
        plugins_dir=tmp_path / "plugins",
        repo_paths={},
        allow_push=False,
        rebase_agent_root=tmp_path / "agent_root",  # never the real one in tests
        rebase_poll_interval=1,
    )


@pytest.fixture()
def trace(tmp_path: Path) -> RunTrace:
    return RunTrace(tmp_path / "trace" / "run_trace.jsonl")


@pytest.fixture()
def fake_agent(monkeypatch, tmp_path: Path, git_repo):
    """Stub the parent vllm-omni-rebase-agent package (which IS importable in
    this venv) so native rebase steps are offline-testable. Returns a control
    dict for scripting results and asserting calls."""
    import json
    import sys
    import types
    from argparse import Namespace

    root = tmp_path / "agent_root"
    (root / "rebase_logs").mkdir(parents=True, exist_ok=True)
    state_file = root / "rebase_logs" / "state.json"

    control: dict = {
        "root": root, "state_file": state_file,
        "module_results": {},   # module -> {"status","exit_code","debug_attempts"}
        "module_calls": [],     # order of node_rebase_module invocations
        "phase_results": {},    # "phase1".."phase5" -> dict returned (or Exception)
        "phase_calls": [],
        "persisted_markers": [],
        "exports": 0,
    }

    class FakeSettings:
        prompts_path = root
        omni_path = git_repo
        vllm_path = git_repo
        rebase_venv = ""
        target_branch = "main"
        last_rebase_vllm_commit = "deadbeef"
        buildkite_api_token = ""
        anthropic_api_key = "test-key"
        wave_1_modules = ["m1", "m2"]
        wave_2_modules = ["m3"]

    def _write_state(update: dict) -> None:
        data = json.loads(state_file.read_text()) if state_file.exists() else {}
        data.update(update)
        state_file.write_text(json.dumps(data))

    orch = types.ModuleType("agent.orchestrator")
    orch.parse_args = lambda argv=None: Namespace(
        local_ci_only="--local-ci-only" in (argv or []),
        remote_ci_only="--remote-ci-only" in (argv or []),
        debug=False, release=False, main_ci_idx=0)
    orch._load_settings = lambda args: FakeSettings()

    def _export(settings):
        control["exports"] += 1
        import os
        os.environ["FAKE_AGENT_EXPORTED"] = str(control["exports"])
    orch._export_all_settings = _export
    orch.detect_baseline = lambda s: s
    orch.make_initial_state = lambda s: {
        "run_id": "rebase-test-0001", "phase": "init", "modules": {},
        "tests": {}, "ci": {}, "errors": [],
        "target_branch": s.target_branch,
        "last_rebase_vllm_commit": s.last_rebase_vllm_commit,
    }

    def _persist(run_id, phase, extra=None):
        control["persisted_markers"].append(phase)
        _write_state({"run_id": run_id, "phase": phase, **(extra or {})})
    orch._persist_state = _persist

    def _find_previous(settings):
        if not state_file.exists():
            return None, None, None
        data = json.loads(state_file.read_text())
        extra = {k: v for k, v in data.items() if k not in ("run_id", "phase")}
        return data.get("run_id"), data.get("phase"), extra
    orch._find_previous_run = _find_previous

    def _setup_logs(settings, run_id):
        log_dir = root / "rebase_logs" / "runs" / run_id
        (log_dir / "agents").mkdir(parents=True, exist_ok=True)
        return log_dir
    orch._setup_log_dirs = _setup_logs
    orch._run_pre_flight_curator = lambda s: control.setdefault("preflight", True)
    orch._run_post_run_curator = lambda s, r, d: control.setdefault("postrun", True)
    orch._git_head_commit = lambda p: "abc1234"

    def _make_phase(name):
        async def wrapper(state):
            control["phase_calls"].append(name)
            result = control["phase_results"].get(name, {})
            if isinstance(result, Exception):
                raise result
            return result
        return wrapper

    subgraphs = types.ModuleType("agent.subgraphs")
    phase_mods = {}
    for i in (1, 3, 4, 5):
        mod = types.ModuleType(f"agent.subgraphs.phase{i}")
        setattr(mod, f"phase{i}_init_wrapper", _make_phase(f"phase{i}"))
        phase_mods[f"agent.subgraphs.phase{i}"] = mod
    p2 = types.ModuleType("agent.subgraphs.phase2")
    p2._save_phase2_progress = lambda run_id, modules: _write_state(
        {"phase2_progress": {"run_id": run_id, "modules": modules}})
    phase_mods["agent.subgraphs.phase2"] = p2

    nodes = types.ModuleType("agent.nodes")
    p2r = types.ModuleType("agent.nodes.phase2_rebase")

    async def node_rebase_module(state):
        module = state.get("module")
        control["module_calls"].append(module)
        result = control["module_results"].get(
            module, {"status": "done", "exit_code": 0, "debug_attempts": 0})
        out = {"modules": {module: dict(result)}}
        if result.get("errors"):
            out["errors"] = result["errors"]
        return out
    p2r.node_rebase_module = node_rebase_module

    dms = types.ModuleType("agent.debug_memory_store")
    dms.init_store = lambda db_path, md_path="": control.setdefault("stores", []).append("dm")
    sks = types.ModuleType("agent.skills_store")
    sks.init_skill_store = lambda d: control.setdefault("stores", []).append("skills")

    pkg = types.ModuleType("agent")
    pkg.orchestrator = orch
    pkg.subgraphs = subgraphs
    modules = {
        "agent": pkg, "agent.orchestrator": orch, "agent.subgraphs": subgraphs,
        "agent.nodes": nodes, "agent.nodes.phase2_rebase": p2r,
        "agent.debug_memory_store": dms, "agent.skills_store": sks,
        **phase_mods,
    }
    for name, mod in modules.items():
        monkeypatch.setitem(sys.modules, name, mod)

    from omni_copilot.engine import rebase_native_steps
    rebase_native_steps._RUNTIME.clear()
    yield control
    rebase_native_steps._RUNTIME.clear()


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """A tiny real git repo with one commit."""
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "test")
    (repo / "mod_a.py").write_text("A = 1\n")
    (repo / "mod_b.py").write_text("B = 1\n")
    git("add", ".")
    git("commit", "-q", "-m", "init")
    return repo
