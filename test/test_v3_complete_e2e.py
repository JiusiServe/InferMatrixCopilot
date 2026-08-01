"""COMPLETE-RUN e2e for the v3 pipeline (post-PR5 gap: every earlier e2e
was a partial — the report-only path, or one cluster at a time).

Two complete runs through the REAL executor over the REAL playbook yaml:

* `local_ci` — a genuinely green end-to-end run to `done`: prelude
  (mode governance + prepared-tree precondition + checkout flock),
  self-cleaning guard with adapter policy, the manifest builder over a
  real nested pipeline, the REAL TestRunner executing real subprocesses,
  the real precommit step, report, finalize. Exit-0 semantics.

* `full` — the whole pipeline to its CURRENT deliberate terminal: wheel
  pick over a real `git clone --shared` upstream scratch (probe faked —
  the only network piece), Dockerfile pin, commit assignment + waves
  (module agent faked at the `rebase_module` boundary — the only LLM
  piece; install faked — the only pip piece), real test loop, real
  precommit, real push gate, then the CI step's deliberate BLOCKED stub
  (EXT1/PR6 wiring). Pins the §3.1 row-3 artifacts: the terminal-report
  finalizer writes RUN_REPORT.md, locks release, the scratch tears down.

Everything else — locks, substate, worktrees, env plans, state handoffs,
when-gates, wave ordering — is production code end to end.
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.engine import lifecycle
from infermatrix_copilot.rebase_engine.modes import resolve_effective_mode
from infermatrix_copilot.rebase_engine.runctx import CheckoutLock
from infermatrix_copilot.rebase_engine.substate import Substate

REPO_ROOT = Path(__file__).resolve().parents[1]


def _git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                    *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture()
def complete_env(settings, tmp_path, monkeypatch):
    """A committed target repo (nested pipelines with REAL runnable
    commands, a pinned CI Dockerfile), a two-commit upstream, and the real
    adapter manifest repointed with a zero-GPU queue map + a trivially
    green precommit so the complete runs execute real subprocesses
    offline."""
    import shutil
    from infermatrix_copilot.engine.executor import Executor
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.steps import register_builtin_steps
    from infermatrix_copilot.playbooks.store import PlaybookStore
    from infermatrix_copilot.run_trace import RunTrace

    repo = tmp_path / "omni"
    (repo / ".buildkite" / "cuda").mkdir(parents=True)
    (repo / "docker").mkdir()
    (repo / "tests").mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / ".buildkite" / "cuda" / "test-merge.yml").write_text(
        yaml.safe_dump({"steps": [
            {"label": "Unit Sweep", "timeout_in_minutes": 1,
             "commands": ["export SWEEP=1", "true"]},
            {"label": "Second Lane", "timeout_in_minutes": 1,
             "commands": ["echo lane-two"]}]}))
    (repo / ".buildkite" / "cuda" / "test-nightly.yml").write_text(
        yaml.safe_dump({"steps": [
            {"label": "Nightly Soak", "timeout_in_minutes": 1,
             "commands": ["true"]}]}))
    (repo / "docker" / "Dockerfile.ci").write_text(
        f"FROM base\nENV VLLM_PRECOMPILED_WHEEL_COMMIT={'a' * 40}\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "seed")

    upstream = tmp_path / "upstream"
    (upstream / "vllm" / "v1" / "worker").mkdir(parents=True)
    _git(upstream, "init", "-q", "-b", "main")
    (upstream / "README").write_text("u")
    _git(upstream, "add", "-A")
    _git(upstream, "commit", "-qm", "baseline")
    (upstream / "vllm" / "v1" / "worker" / "w.py").write_text("w = 1\n")
    _git(upstream, "add", "-A")
    _git(upstream, "commit", "-qm", "worker change")
    shas = subprocess.run(["git", "log", "--format=%H", "--reverse"],
                          cwd=upstream, capture_output=True, text=True,
                          check=True).stdout.split()
    baseline_sha, head_sha = shas[0], shas[-1]

    adir = Path(settings.adapters_dir) / "vllm_omni"
    adir.mkdir(parents=True, exist_ok=True)
    manifest = yaml.safe_load(
        (REPO_ROOT / "adapters/vllm_omni/manifest.yaml").read_text())
    manifest["repo"]["path"] = str(repo)
    # zero-GPU queue so the runner EXECUTES the commands on a GPU-less box
    # instead of hw-skipping them
    manifest["rebase"]["test_manifest"]["queue_map"] = {
        "gpu_1_queue": [0, "any"]}
    manifest["rebase"]["precommit"]["command"] = "true"
    (adir / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    shutil.copytree(REPO_ROOT / "adapters" / "vllm_omni" / "rebase",
                    adir / "rebase")
    settings.playbooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "playbooks" / "repo-rebase-v3.yaml",
                settings.playbooks_dir / "repo-rebase-v3.yaml")

    monkeypatch.setenv("VLLM_OMNI_VENV", str(tmp_path / "omni-venv"))
    monkeypatch.setenv("VLLM_UPSTREAM_REPO", str(upstream))
    registry = register_builtin_steps(StepRegistry())
    store = PlaybookStore(settings.playbooks_dir, registry)

    def make_run(name):
        run_dir = tmp_path / name
        run_dir.mkdir()
        executor = Executor(registry, settings, run_dir=run_dir,
                            trace=RunTrace(run_dir / "trace.jsonl"))
        return executor, run_dir

    return SimpleNamespace(repo=repo, upstream=upstream,
                           baseline=baseline_sha, head=head_sha,
                           playbook=store.get("repo-rebase-v3"),
                           make_run=make_run)


def _state_for(env, run_dir, params):
    spec = SimpleNamespace(params=dict(params), report_only=False)
    resolve_effective_mode(spec)
    return {"task_spec": {"kind": "repo_rebase", "repo": "vllm-omni",
                          "mode": "eco", "params": spec.params},
            "repo_path": str(env.repo), "run_id": run_dir.name}


def test_local_ci_complete_run_green(complete_env):
    """A COMPLETE local_ci run to `done`: real guard, real manifest build,
    real subprocess test execution, real precommit, report + finalize —
    the first end-to-end green run of the merged pipeline."""
    env = complete_env
    executor, run_dir = env.make_run("run-localci")
    state = _state_for(env, run_dir, {"rebase_mode": "local_ci"})
    outcome = asyncio.run(executor.run(env.playbook, state))
    assert outcome.status == "done", getattr(outcome, "blocked_reason", "")
    # the local loop RAN the jobs (not skipped): both merge-pipeline lanes
    # passed, the nightly lane stayed out of the local loop
    data = Substate(run_dir, run_dir.name).read()
    assert data["tests"]["pipeline"]["passed"] == 2
    assert data["tests"]["pipeline"]["failed"] == 0
    assert data["tests"].get("infra_failures", []) == []
    assert data["tests"]["precommit"]["result"] == "passed"
    assert data["phase"] == "done"
    # report exists from the report step (not the fallback finalizer)
    assert (run_dir / "RUN_REPORT.md").exists()
    # the run held the shared checkout flock; the lifecycle finalizer
    # releases it (exit-0 path)
    probe = CheckoutLock(env.repo, "omni")
    assert probe.acquire(blocking=False) is False
    asyncio.run(lifecycle.finalize(run_dir, outcome))
    assert probe.acquire(blocking=False) is True
    probe.release()


def test_full_mode_complete_run_to_current_terminal(complete_env,
                                                    monkeypatch):
    """The COMPLETE full pipeline to its CURRENT terminal: wheel pick over
    the real scratch clone + Dockerfile pin, real commit assignment, the
    wave fan-out (module agent faked at the rebase_module boundary), real
    tests + precommit + push gate — then the deliberate CI stub BLOCKS
    (EXT1/PR6). Pins §3.1 row 3: RUN_REPORT via the terminal-report
    finalizer, lock release, scratch teardown."""
    env = complete_env
    from infermatrix_copilot.engine.steps import rebase_v3
    from infermatrix_copilot.rebase_engine import module_rebase as mr

    monkeypatch.setattr(rebase_v3.wheel_mod, "make_arch_probe",
                        lambda spec: (lambda c: True))   # the network piece
    installs = {}

    def fake_install(up, commit, spec, *, python, **kw):
        installs.update({"commit": commit, "python": python})
        return True
    monkeypatch.setattr(rebase_v3.wheel_mod, "ensure_wheel_installed",
                        fake_install)                     # the pip piece
    monkeypatch.setattr(
        rebase_v3, "_tier_client",
        lambda ctx: (object(), SimpleNamespace(
            model="m-test", api_key="k", base_url="", source="tier:eco")))
    agent_calls = []

    async def fake_rebase_module(module, **kw):           # the LLM piece
        agent_calls.append(module)
        kw["substate"].update({"modules": {module: {
            "status": "done", "exit_code": 0, "debug_attempts": 0}}})
        return {"status": "done", "exit_code": 0, "debug_attempts": 0,
                "turns": 1, "summary": ""}
    monkeypatch.setattr(mr, "rebase_module", fake_rebase_module)

    executor, run_dir = env.make_run("run-full")
    state = _state_for(env, run_dir, {
        "rebase_mode": "full", "last_rebase_commit": env.baseline,
        "force_upstream_commit": env.head})
    outcome = asyncio.run(executor.run(env.playbook, state))

    # today's deliberate terminal: BLOCKED at the CI provider stub
    assert outcome.status == "blocked"
    assert "provider" in outcome.blocked_reason.lower() \
        or "CI" in outcome.blocked_reason
    # everything BEFORE the stub completed for real
    ok_steps = {sid for sid, r in outcome.step_results.items() if r.ok}
    assert {"prelude", "guard", "wheel", "assign", "wave1", "wave_gate",
            "wave2", "tests", "precommit", "push_gate"} <= ok_steps
    # wheel: picked the forced commit, pinned the Dockerfile, "installed"
    # into the target venv — and operated on the SCRATCH clone
    assert installs["commit"] == env.head
    assert installs["python"].endswith("omni-venv/bin/python")
    assert env.head in (env.repo / "docker" / "Dockerfile.ci").read_text()
    assert state["upstream_path"].startswith(str(run_dir))
    assert state["upstream_origin_path"] == str(env.upstream)
    # assignment routed the worker change; the wave fan-out ran the agent
    assert state["wave1_modules"] == ["worker_runner"]
    assert agent_calls == ["worker_runner"]
    data = Substate(run_dir, run_dir.name).read()
    assert data["modules"]["worker_runner"]["status"] == "done"
    assert data["tests"]["pipeline"]["passed"] == 2
    assert data["tests"]["precommit"]["result"] == "passed"
    assert data["upstream_commit"] == env.head
    # §3.1 row 3: blocked BEFORE the report step — the terminal-report
    # finalizer supplies RUN_REPORT; locks release; the scratch tears down
    assert not (run_dir / "RUN_REPORT.md").exists()
    asyncio.run(lifecycle.finalize(run_dir, outcome))
    report = (run_dir / "RUN_REPORT.md").read_text()
    assert "status: blocked" in report and "rebase_mode: full" in report
    for checkout, name in ((env.repo, "omni"), (env.upstream, "upstream")):
        probe = CheckoutLock(checkout, name)
        assert probe.acquire(blocking=False) is True, name
        probe.release()
    assert not (run_dir / "upstream_scratch").exists()