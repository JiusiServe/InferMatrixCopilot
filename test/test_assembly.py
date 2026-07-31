"""PR4c — assembly: mode governance, push-gate taxonomy, manifest builder,
test loop, CI build ledger + monitor, v1 obligations, and the v3 playbook
partial e2e (report_only end-to-end; full-mode terminal row)."""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from infermatrix_copilot.rebase_engine import ci_loop, test_loop as tl
from infermatrix_copilot.rebase_engine.modes import (
    ModeConflictError, mode_state_flags, resolve_effective_mode)
from infermatrix_copilot.rebase_engine.push_gate import evaluate_push_gate
from infermatrix_copilot.rebase_engine.substate import Substate
from infermatrix_copilot.rebase_engine.test_manifest import (
    ManifestSpec, build_manifest)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _spec(params=None, report_only=False):
    return SimpleNamespace(params=dict(params or {}),
                           report_only=report_only)


# -- mode governance -----------------------------------------------------------

def test_mode_truth_table():
    """Every cell of the Rev 8 §2.1 table, including the write-back."""
    for raw, expect in [("", "report_only"), ("report_only", "report_only"),
                        ("full", "full"), ("local_ci", "local_ci"),
                        ("remote_ci", "remote_ci")]:
        s = _spec({"rebase_mode": raw} if raw else {})
        assert resolve_effective_mode(s) == expect
        assert s.params["rebase_mode"] == expect          # write-back
        assert s.report_only == (expect == "report_only")  # one truth
    # report_only=True narrows: unset/report_only fine, mutating BLOCKED
    for raw in ("", "report_only"):
        s = _spec({"rebase_mode": raw} if raw else {}, report_only=True)
        assert resolve_effective_mode(s) == "report_only"
    for raw in ("full", "local_ci", "remote_ci"):
        with pytest.raises(ModeConflictError, match="narrowing"):
            resolve_effective_mode(_spec({"rebase_mode": raw},
                                         report_only=True))
    with pytest.raises(ModeConflictError, match="unknown rebase_mode"):
        resolve_effective_mode(_spec({"rebase_mode": "yolo"}))
    assert mode_state_flags("full") == {
        "mode_report_only": False, "mode_full": True,
        "mode_local_ci": False, "mode_remote_ci": False}


def test_locked_playbook_is_not_mode_governed(tmp_path):
    """The LOCKED delegating playbook does not declare mode_aware, so
    resolve_effective_mode never touches its specs — byte-identical
    behavior (recorded refinement of Rev 8 §2.1)."""
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.steps import register_builtin_steps
    from infermatrix_copilot.playbooks.store import PlaybookStore
    store = PlaybookStore(REPO_ROOT / "playbooks",
                          register_builtin_steps(StepRegistry()))
    assert store.get("repo-rebase").mode_aware is False
    assert store.get("repo-rebase-v3").mode_aware is True
    assert store.get("repo-rebase-native-v1").mode_aware is True
    assert store.get("repo-rebase-v3").status == "candidate"  # planner-invisible


# -- push gate taxonomy --------------------------------------------------------

def test_push_gate_taxonomy():
    base = {"modules": {"a": {"status": "done"}},
            "tests": {"pipeline": {"failed_tests": []},
                      "precommit": {"result": "passed"}}}
    assert evaluate_push_gate(base, {}).allowed

    structural = {"modules": {"a": {"status": "failed"}},
                  "tests": {"pipeline": {"failed_tests": ["t1"]},
                            "precommit": {"result": "passed"}}}
    d = evaluate_push_gate(structural, {})
    assert not d.allowed and any("module a failed" in r for r in d.reasons)
    # explicit push_with_failures: structural passes, loudly
    d = evaluate_push_gate(structural, {"push_with_failures": True})
    assert d.allowed and any("explicit" in r for r in d.reasons)

    # assertion failures pass through FLAGGED
    asserts = {"modules": {}, "tests": {"pipeline": {"failed_tests": ["t1"]},
                                        "precommit": {"result": "passed"}}}
    d = evaluate_push_gate(asserts, {})
    assert d.allowed and d.flagged == ("test failure: t1",)
    # strict makes them blocking
    d = evaluate_push_gate(asserts, {"strict_push_gate": True})
    assert not d.allowed and "strict gate" in d.reasons[0]
    # infra failures are STRUCTURAL, never ordinary test failures
    infra = {"tests": {"infra_failures": ["harness crash"],
                       "pipeline": {}, "precommit": {}}}
    assert not evaluate_push_gate(infra, {}).allowed
    with pytest.raises(ModeConflictError, match="conflict"):
        evaluate_push_gate(base, {"strict_push_gate": True,
                                  "push_with_failures": True})


# -- test manifest -------------------------------------------------------------

@pytest.fixture()
def ci_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".buildkite").mkdir(parents=True)
    (repo / "tests" / "worker").mkdir(parents=True)
    (repo / "tests" / "worker" / "test_a_expansion.py").write_text("x")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / ".buildkite" / "test-merge.yml").write_text(yaml.safe_dump({
        "steps": [
            {"label": "Worker Tests", "timeout_in_minutes": 10,
             "agents": {"queue": "gpu_4_queue"},
             "commands": ["export FOO=1",
                          "pytest tests/worker/test_a.py"]},
            {"label": "Perf sweep", "commands": ["x"]},          # skipped
            {"group": "g", "steps": [
                {"label": "K8s Job", "agents": {"queue": "mithril-h100-pool"},
                 "plugins": [{"kubernetes": {"podSpec": {"containers": [
                     {"resources": {"limits": {"nvidia.com/gpu": "8"}}}]}}}],
                 "commands": ["pytest tests/worker/"]}]},
        ]}))
    (repo / ".buildkite" / "test-ready.yml").write_text(yaml.safe_dump({
        "steps": [{"label": "Worker Tests", "timeout_in_minutes": 20,
                   "agents": {"queue": "gpu_1_queue"},
                   "commands": ["pytest tests/worker/test_a.py"]}]}))
    return repo


def test_manifest_build(ci_repo):
    manifest = yaml.safe_load(
        (REPO_ROOT / "adapters/vllm_omni/manifest.yaml").read_text())
    spec = ManifestSpec.from_manifest(manifest)
    built = build_manifest(ci_repo, spec)
    by_slug = {j.slug: j for j in built.jobs}
    assert "perf_sweep" not in by_slug                     # skip pattern
    wt = by_slug["worker_tests"]
    assert wt.source == "ready" and wt.timeout_sec == 1200  # ready wins slug
    assert wt.env == "" or "FOO" not in wt.command          # env split out
    # rename-family path correction: test_a.py -> test_a_expansion.py
    assert "tests/worker/test_a_expansion.py" in wt.command
    k8s = by_slug["k8s_job"]
    assert k8s.min_gpus == 8                                # pod spec wins
    assert wt.module == "worker_runner"                     # manifest map
    assert "worker_runner" in built.module_plans


# -- test loop -----------------------------------------------------------------

def test_test_loop_decision_matrix(tmp_path):
    sub = Substate(tmp_path, "run-1")
    jobs = [{"slug": s, "label": s, "min_gpus": 1}
            for s in ("pass", "hwskip", "preexisting", "regression_fixed",
                      "regression_stuck", "infra")]
    runs = {"pass": tl.TestRunResult(0),
            "hwskip": tl.TestRunResult(0, skipped=True, skip_reason="gpu"),
            "preexisting": tl.TestRunResult(1),
            "regression_fixed": tl.TestRunResult(1),
            "regression_stuck": tl.TestRunResult(1),
            "infra": tl.TestRunResult(1)}
    baselines = {"preexisting": tl.TestRunResult(1),       # fails on main too
                 "regression_fixed": tl.TestRunResult(0),
                 "regression_stuck": tl.TestRunResult(0),
                 "infra": None}                            # worktree broken
    debugs = {"regression_fixed": True, "regression_stuck": False,
              "infra": False}
    debugged = []

    async def debug_fn(slug, label, rc, output):
        debugged.append(slug)
        return debugs[slug]

    result = asyncio.run(tl.run_test_loop(
        jobs, substate=sub, run_fn=lambda s: runs[s],
        baseline_fn=lambda s: baselines[s], debug_fn=debug_fn))
    assert result["passed"] == 2                 # pass + regression_fixed
    assert result["failed_tests"] == ["regression_stuck", "infra"]
    assert sorted(result["skipped_tests"]) == ["hwskip", "preexisting"]
    # baseline-None (infra) went to DEBUG, not to skipped — a git error
    # must never mask a regression
    assert "infra" in debugged and "preexisting" not in debugged
    # resume: a second loop skips everything already settled
    reran = []
    result2 = asyncio.run(tl.run_test_loop(
        jobs, substate=sub,
        run_fn=lambda s: reran.append(s) or runs[s],
        baseline_fn=lambda s: baselines[s], debug_fn=debug_fn))
    assert result2["passed"] >= 2 and "pass" not in reran


# -- CI build ledger + monitor -------------------------------------------------

class FakeCI:
    def __init__(self):
        self.builds: dict[str, dict] = {}
        self.created = 0
        self.logs: dict[tuple, str] = {}

    def create_build(self, *, branch, commit, message, meta_data):
        self.created += 1
        bid = f"b{self.created}"
        self.builds[bid] = {"id": bid, "web_url": f"u/{bid}",
                            "state": "running", "meta_data": dict(meta_data),
                            "jobs": []}
        return self.builds[bid]

    def get_build(self, build_id):
        return self.builds[build_id]

    def find_builds_by_meta(self, key, value):
        return [b for b in self.builds.values()
                if b["meta_data"].get(key) == value]

    def cancel_build(self, build_id):
        self.builds[build_id]["state"] = "canceled"
        return self.builds[build_id]

    def get_job_log(self, build_id, job_id):
        return self.logs.get((build_id, job_id), "")


def test_build_op_guarded_create_and_recovery(tmp_path):
    ci = FakeCI()
    op = ci_loop.create_build_guarded(
        ci, tmp_path, op_id="op-1", run_id="r", purpose="initial",
        branch="ci-x", commit="c" * 40, message="m")
    assert op.state == "created" and op.build_id == "b1"
    assert ci.builds["b1"]["meta_data"]["imx_op_id"] == "op-1"
    # idempotent: the created record short-circuits, no second build
    op2 = ci_loop.create_build_guarded(
        ci, tmp_path, op_id="op-1", run_id="r", purpose="initial",
        branch="ci-x", commit="c" * 40, message="m")
    assert op2.build_id == "b1" and ci.created == 1

    # crash window: intent durable, create landed, ack lost — recovery
    # ADOPTS by exact op id instead of re-creating
    intent = ci_loop.BuildOp(op_id="op-2", run_id="r", purpose="retry",
                             branch="ci-x", commit="c" * 40)
    ci_loop._durable_write(intent.path(tmp_path),
                           ci_loop.__dict__["asdict"](intent))
    orphan = ci.create_build(branch="ci-x", commit="c" * 40, message="m",
                             meta_data={"imx_op_id": "op-2"})
    op3 = ci_loop.create_build_guarded(
        ci, tmp_path, op_id="op-2", run_id="r", purpose="retry",
        branch="ci-x", commit="c" * 40, message="m", sleep=lambda s: None)
    assert op3.build_id == orphan["id"] and ci.created == 2  # adopted

    # zero matches after bounded re-poll ⇒ ESCALATE, never re-create
    intent = ci_loop.BuildOp(op_id="op-3", run_id="r", purpose="retry",
                             branch="ci-x", commit="c" * 40)
    ci_loop._durable_write(intent.path(tmp_path),
                           ci_loop.__dict__["asdict"](intent))
    with pytest.raises(ci_loop.CIOpError, match="refusing to re-create"):
        ci_loop.create_build_guarded(
            ci, tmp_path, op_id="op-3", run_id="r", purpose="retry",
            branch="ci-x", commit="c" * 40, message="m",
            sleep=lambda s: None)
    assert ci.created == 2

    # cancellation only for op-recorded builds
    assert ci_loop.cancel_build_guarded(ci, tmp_path, "op-1") is True
    assert ci.builds["b1"]["state"] == "canceled"
    assert ci_loop.cancel_build_guarded(ci, tmp_path, "op-nope") is False


def test_monitor_classification(tmp_path):
    ci = FakeCI()
    b = ci.create_build(branch="x", commit="c" * 40, message="m",
                        meta_data={})
    spec = ci_loop.CIClassifySpec(
        ignorable_name_patterns=("(?i)statistics",),
        ignorable_log_patterns=("401 Unauthorized",))
    b["state"] = "failed"
    b["jobs"] = [
        {"name": "Good Job", "id": "j1", "state": "passed", "exit_status": 0},
        {"name": "Testcase Statistics", "id": "j2", "state": "failed",
         "exit_status": 1},
        {"name": "Gated Model", "id": "j3", "state": "failed",
         "exit_status": 1},
        {"name": "Real Failure", "id": "j4", "state": "failed",
         "exit_status": 2},
        {"name": "Budget Kill", "id": "j5", "state": "timed_out",
         "exit_status": 255},
    ]
    ci.logs[(b["id"], "j3")] = "fatal: 401 Unauthorized"
    ci.logs[(b["id"], "j4")] = "FAILED tests/x.py::test_y - boom"
    ci.logs[(b["id"], "j5")] = (
        "\x1b_bk;t=1000000\x07 dozens of tests executed and PASSED with "
        "healthy streaming output right up to the budget wall\n"
        "\x1b_bk;t=1200000\x07 Exceeded maximum job timeout")
    out = ci_loop.monitor_build(ci, b["id"], spec=spec, poll_sec=0,
                                sleep=lambda s: None)
    cls = {j.name: j.classification for j in out.jobs}
    assert cls == {"Good Job": "passed", "Testcase Statistics": "ignored",
                   "Gated Model": "ignored", "Real Failure": "failed",
                   "Budget Kill": "budget_timeout"}
    assert [j.name for j in out.failed_jobs] == ["Real Failure"]
    # no-run build states are TERMINAL, neither success nor failure
    b["state"] = "not_run"
    out = ci_loop.monitor_build(ci, b["id"], spec=spec, poll_sec=0,
                                sleep=lambda s: None)
    assert out.no_run and out.jobs == []


def test_pure_log_classifiers():
    line = "\x1b_bk;t=123\x07[2026-07-01T10:00:00Z] \x1b[31mFAILED\x1b[0m " \
           "tests/a.py::test_x - took 1.25s"
    n = ci_loop.normalize_log_line(line)
    assert n == "FAILED tests/a.py::test_x - took <N>s"
    ids = ci_loop.extract_failed_test_ids(line)
    assert ids == {"tests/a.py::test_x"}
    sig = ci_loop.extract_error_signature(
        "RuntimeError: boom at 3.14s\nFAILED tests/a.py::test_x - x",
        extra_exception_names=("MyCustomError",))
    assert "RuntimeError: boom at <N>s" in sig
    assert ci_loop.is_budget_timeout(
        "\x1b_bk;t=1000000\x07 many tests ran here and PASSED cleanly "
        "with plenty of output before the kill\n\x1b_bk;t=1100000\x07 "
        "Received cancellation signal")
    assert not ci_loop.is_budget_timeout("FAILED then "
                                         "Received cancellation signal PASSED")


# -- scrub wiring --------------------------------------------------------------

def test_scrubbed_agent_env_wiring(monkeypatch):
    from infermatrix_copilot.rebase_engine.testing_env import \
        scrubbed_agent_env
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret")
    monkeypatch.setenv("PATH", "/usr/bin")
    env = scrubbed_agent_env({"EXTRA": "1"})
    assert "ANTHROPIC_API_KEY" not in env
    assert env["PATH"] == "/usr/bin" and env["EXTRA"] == "1"
    import os
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-secret"   # never mutated


# -- v3 playbook partial e2e ---------------------------------------------------

@pytest.fixture()
def v3_env(settings, tmp_path):
    import shutil
    from infermatrix_copilot.engine.executor import Executor
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.steps import register_builtin_steps
    from infermatrix_copilot.playbooks.store import PlaybookStore
    # fixture repo with a .buildkite pipeline
    repo = tmp_path / "omni"
    (repo / ".buildkite").mkdir(parents=True)
    (repo / "tests").mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / ".buildkite" / "test-merge.yml").write_text(yaml.safe_dump({
        "steps": [{"label": "Quick", "timeout_in_minutes": 1,
                   "commands": ["true"]}]}))
    # adapter: the real manifest, repointed
    adir = Path(settings.adapters_dir) / "vllm_omni"
    adir.mkdir(parents=True, exist_ok=True)
    manifest = yaml.safe_load(
        (REPO_ROOT / "adapters/vllm_omni/manifest.yaml").read_text())
    manifest["repo"]["path"] = str(repo)
    (adir / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    settings.playbooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "playbooks" / "repo-rebase-v3.yaml",
                settings.playbooks_dir / "repo-rebase-v3.yaml")
    from infermatrix_copilot.run_trace import RunTrace
    registry = register_builtin_steps(StepRegistry())
    store = PlaybookStore(settings.playbooks_dir, registry)
    run_dir = tmp_path / "run-v3"
    run_dir.mkdir()
    executor = Executor(registry, settings, run_dir=run_dir,
                        trace=RunTrace(run_dir / "trace.jsonl"))
    return executor, store.get("repo-rebase-v3"), repo, run_dir


def test_v3_report_only_partial_e2e(v3_env, tmp_path, settings, trace):
    """report_only end to end: prelude seeds mode flags, the mutating guard
    and full-mode steps are when-gated OFF, the scan writes the manifest
    artifact, finalize passes on clean substate."""
    executor, playbook, repo, run_dir = v3_env
    spec = SimpleNamespace(params={"rebase_mode": ""}, report_only=False)
    resolve_effective_mode(spec)
    state = {"task_spec": {"kind": "repo_rebase", "repo": "vllm-omni",
                           "params": spec.params},
             "repo_path": str(repo), "run_id": "run-e2e"}
    outcome = asyncio.run(executor.run(playbook, state))
    assert outcome.status == "done", getattr(outcome, "blocked_reason", "")
    data = json.loads((run_dir / "test_manifest.json").read_text())
    assert data["jobs"] and data["jobs"][0]["slug"] == "quick"
    # the when-gates held: no guard/wheel artifacts in a report_only run
    assert state.get("mode_report_only") is True
    assert state.get("mode_full") is False


def test_v3_finalize_terminal_row(v3_env, settings):
    """Rev 8 §3.1 row 2: all steps ok but substate failures ⇒ BLOCKED (the
    reused needs-human exit-3 semantics)."""
    executor, playbook, repo, _ = v3_env
    from infermatrix_copilot.engine.step import StepContext
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.steps import register_builtin_steps
    from infermatrix_copilot.run_trace import RunTrace
    registry = register_builtin_steps(StepRegistry())
    fin = registry.get("rebase.v3_finalize")
    run_dir = Path(settings.run_root) / "run-fin"
    run_dir.mkdir(parents=True, exist_ok=True)
    sub = Substate(run_dir, "run-fin")
    sub.update({"modules": {"worker": {"status": "failed"}}})
    ctx = StepContext(settings=settings, state={"run_id": "run-fin"},
                      params={}, run_dir=run_dir,
                      trace=RunTrace(run_dir / "trace.jsonl"))
    result = asyncio.run(fin.handler(ctx))
    assert not result.ok
    assert "needing a human" in result.summary
    # ...and a clean substate finalizes ok
    run_dir2 = Path(settings.run_root) / "run-fin2"
    run_dir2.mkdir(parents=True, exist_ok=True)
    Substate(run_dir2, "run-fin2").update({"modules": {"a": {"status": "done"}}})
    ctx2 = StepContext(settings=settings, state={"run_id": "run-fin2"},
                       params={}, run_dir=run_dir2,
                       trace=RunTrace(run_dir2 / "trace.jsonl"))
    assert asyncio.run(fin.handler(ctx2)).ok
