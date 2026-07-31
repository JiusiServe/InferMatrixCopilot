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
        "mode_local_ci": False, "mode_remote_ci": False,
        "mode_runs_local_tests": True, "mode_runs_push_gate": True,
        "mode_runs_remote_ci": True}
    # the composites encode the §2.2 or-of-modes (single-key `when:`)
    assert mode_state_flags("local_ci")["mode_runs_local_tests"] is True
    assert mode_state_flags("local_ci")["mode_runs_push_gate"] is False
    assert mode_state_flags("local_ci")["mode_runs_remote_ci"] is False
    assert mode_state_flags("remote_ci")["mode_runs_local_tests"] is False
    assert mode_state_flags("remote_ci")["mode_runs_push_gate"] is True
    assert mode_state_flags("report_only")["mode_runs_push_gate"] is False


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


def test_test_loop_infra_is_structural(tmp_path):
    """Rev 8 §2.3: timeouts/watchdog kills are INFRASTRUCTURE failures —
    kept out of `failed_tests` (assertion pass-through), never sent to the
    baseline split or the debug agent, and sticky across resume."""
    sub = Substate(tmp_path, "run-i")
    jobs = [{"slug": s, "label": s, "min_gpus": 1}
            for s in ("timeout", "assertion")]
    runs = {"timeout": tl.TestRunResult(1, infra="timeout"),
            "assertion": tl.TestRunResult(1)}
    baselined, debugged = [], []

    async def debug_fn(slug, label, rc, output):
        debugged.append(slug)
        return False

    def baseline_fn(slug):
        baselined.append(slug)
        return tl.TestRunResult(0)

    result = asyncio.run(tl.run_test_loop(
        jobs, substate=sub, run_fn=lambda s: runs[s],
        baseline_fn=baseline_fn, debug_fn=debug_fn))
    assert result["infra_failures"] == ["timeout: timeout"]
    assert result["failed_tests"] == ["assertion"]     # infra NOT here
    assert result["failed"] == 2
    assert baselined == ["assertion"] and debugged == ["assertion"]
    # resume: the recorded infra failure is not re-run (a lucky second
    # attempt must not flip a structural failure into a pass)
    reran = []
    result2 = asyncio.run(tl.run_test_loop(
        jobs, substate=sub, run_fn=lambda s: reran.append(s) or runs[s],
        baseline_fn=baseline_fn, debug_fn=debug_fn))
    assert "timeout" not in reran
    assert result2["infra_failures"] == ["timeout: timeout"]


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
                   "commands": ["export QUICK_ENV=1", "true"]}]}))
    (repo / ".buildkite" / "test-nightly.yml").write_text(yaml.safe_dump({
        "steps": [{"label": "Nightly Soak", "timeout_in_minutes": 1,
                   "commands": ["true"]}]}))
    # committed clean tree: report_only runs the read-only guard_clean
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-qm", "init"], cwd=repo, check=True)
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
    # the honest terminal name — not "done" — is what substate records
    assert Substate(run_dir, "run-fin").get("phase") == "needs_human"
    # ...and a clean substate finalizes ok
    run_dir2 = Path(settings.run_root) / "run-fin2"
    run_dir2.mkdir(parents=True, exist_ok=True)
    Substate(run_dir2, "run-fin2").update({"modules": {"a": {"status": "done"}}})
    ctx2 = StepContext(settings=settings, state={"run_id": "run-fin2"},
                       params={}, run_dir=run_dir2,
                       trace=RunTrace(run_dir2 / "trace.jsonl"))
    assert asyncio.run(fin.handler(ctx2)).ok


# -- v3 per-mode matrix + runtime init -----------------------------------------

def test_v3_per_mode_matrix():
    """The playbook's `when:` gates realize the Rev 8 §2.2 matrix exactly:
    report_only gets the read-only guard + scan; local_ci runs the local
    loop but a VACUOUS push gate; remote_ci pushes without the local loop;
    full runs everything. Report precedes finalize (terminal row must not
    suppress RUN_REPORT); waves are ordered around the gate."""
    from infermatrix_copilot.engine.executor import _eval_when
    doc = yaml.safe_load(
        (REPO_ROOT / "playbooks" / "repo-rebase-v3.yaml").read_text())
    matrix = {
        "report_only": {"prelude", "guard_check", "scan", "report",
                        "finalize"},
        "local_ci": {"prelude", "guard", "tests", "report", "finalize"},
        "remote_ci": {"prelude", "guard", "push_gate", "ci", "report",
                      "finalize"},
        "full": {"prelude", "guard", "wheel", "assign", "wave1",
                 "wave_gate", "wave2", "tests", "push_gate", "ci",
                 "report", "finalize"},
    }
    for mode, expect in matrix.items():
        state = {"task_spec": {}, **mode_state_flags(mode)}
        ran = {s["id"] for s in doc["steps"]
               if "when" not in s or _eval_when(s["when"], state)}
        assert ran == expect, f"{mode}: {sorted(ran ^ expect)}"
    ids = [s["id"] for s in doc["steps"]]
    assert ids.index("report") < ids.index("finalize")
    assert ids.index("wave1") < ids.index("wave_gate") < ids.index("wave2")


def test_v3_prelude_inits_runtime(v3_env, settings, trace, tmp_path,
                                  monkeypatch):
    """Mutating modes acquire the shared checkout flock(s) (name from
    adapter data), publish `upstream_path`/`last_rebase_upstream_commit`,
    and release the locks via the lifecycle finalizer on EVERY exit path;
    full mode without its preconditions is BLOCKED upfront."""
    from infermatrix_copilot.engine import lifecycle
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.step import StepContext
    from infermatrix_copilot.engine.steps import register_builtin_steps
    from infermatrix_copilot.rebase_engine.runctx import CheckoutLock
    _, _, repo, run_dir = v3_env
    monkeypatch.delenv("VLLM_UPSTREAM_REPO", raising=False)
    registry = register_builtin_steps(StepRegistry())
    prelude = registry.get("rebase.v3_prelude")
    upstream = tmp_path / "upstream"
    upstream.mkdir()

    def ctx_for(params, run_dir):
        return StepContext(
            settings=settings, params={}, run_dir=run_dir, trace=trace,
            state={"task_spec": {"kind": "repo_rebase", "repo": "vllm-omni",
                                 "params": params},
                   "repo_path": str(repo), "run_id": run_dir.name})

    # full without upstream/baseline: BLOCKED before any lock is taken
    r = asyncio.run(prelude.handler(
        ctx_for({"rebase_mode": "full"}, run_dir)))
    assert not r.ok and "upstream" in r.summary
    assert not (repo / "locks" / "omni.lock").exists()

    # full with both: locks acquired (adapter lock_name + upstream),
    # world published, and the finalizer releases them — upstream seeded
    # via state instead of the env var
    ctx = ctx_for({"rebase_mode": "full", "last_rebase_commit": "d" * 40},
                  run_dir)
    ctx.state["upstream_path"] = str(upstream)
    r = asyncio.run(prelude.handler(ctx))
    assert r.ok, r.summary
    ups = r.outputs["state_updates"]
    assert ups["upstream_path"] == str(upstream)
    assert ups["last_rebase_upstream_commit"] == "d" * 40
    assert ups["mode_runs_push_gate"] is True
    # both flocks held: a second taker fails
    probe = CheckoutLock(repo, "omni")
    assert probe.acquire(blocking=False) is False
    probe_up = CheckoutLock(upstream, "upstream")
    assert probe_up.acquire(blocking=False) is False
    # the lifecycle finalizer releases on every exit path
    asyncio.run(lifecycle.finalize(run_dir, None))
    assert probe.acquire(blocking=False) is True
    probe.release()
    assert probe_up.acquire(blocking=False) is True
    probe_up.release()

    # report_only never locks
    run_dir2 = run_dir.parent / "run-ro"
    run_dir2.mkdir(exist_ok=True)
    r = asyncio.run(prelude.handler(
        ctx_for({"rebase_mode": "report_only"}, run_dir2)))
    assert r.ok
    assert lifecycle._finalizers.get(str(run_dir2)) is None


def test_v3_wave_gate(v3_env, settings, trace):
    """A wave-1 module failure empties wave 2 (dependents never build on a
    broken base); halt_on_module_failure escalates instead."""
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.step import FailureKind, StepContext
    from infermatrix_copilot.engine.steps import register_builtin_steps
    _, _, repo, run_dir = v3_env
    registry = register_builtin_steps(StepRegistry())
    gate = registry.get("rebase.v3_wave_gate")
    sub = Substate(run_dir, "run-w")
    sub.update({"modules": {"m1": {"status": "failed"},
                            "m2": {"status": "done"}}})

    def ctx_for(params):
        return StepContext(
            settings=settings, params={}, run_dir=run_dir, trace=trace,
            state={"task_spec": {"params": params}, "run_id": "run-w",
                   "wave1_modules": ["m1", "m2"],
                   "wave2_modules": ["m3"]})

    r = asyncio.run(gate.handler(ctx_for({})))
    assert r.ok and r.outputs["state_updates"]["wave2_modules"] == []
    r = asyncio.run(gate.handler(ctx_for({"halt_on_module_failure": True})))
    assert not r.ok and r.failure is FailureKind.ESCALATE
    # clean wave 1 leaves wave 2 alone
    sub.update({"modules": {"m1": {"status": "done"}}})
    r = asyncio.run(gate.handler(ctx_for({})))
    assert r.ok and "state_updates" not in (r.outputs or {})


def test_v3_assign_publishes_waves(v3_env, settings, trace, monkeypatch):
    """The assign step orders active modules into the manifest's wave lists
    — the playbook's wave1/wave2 fan-outs depend on them."""
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.step import StepContext
    from infermatrix_copilot.engine.steps import rebase_v3, \
        register_builtin_steps
    _, _, repo, run_dir = v3_env
    manifest = yaml.safe_load(
        (Path(settings.adapters_dir) / "vllm_omni" / "manifest.yaml")
        .read_text())
    modules = list(manifest["modules"])
    active = modules[:3]
    monkeypatch.setattr(
        rebase_v3, "run_commit_assignment",
        lambda cfg, paths, sub: SimpleNamespace(
            total_commits=7,
            skip={m: (m not in active) for m in modules}))
    registry = register_builtin_steps(StepRegistry())
    ctx = StepContext(
        settings=settings, params={}, run_dir=run_dir, trace=trace,
        state={"task_spec": {"repo": "vllm-omni", "params": {}},
               "run_id": "run-a", "repo_path": str(repo),
               "upstream_path": str(repo),
               "last_rebase_upstream_commit": "d" * 40})
    r = asyncio.run(registry.get("rebase.v3_assign").handler(ctx))
    assert r.ok, r.summary
    ups = r.outputs["state_updates"]
    exp_w1 = [m for m in modules if m in active
              and (manifest["modules"][m] or {}).get("wave") == 1]
    exp_w2 = [m for m in active if m not in exp_w1]
    assert ups["wave1_modules"] == exp_w1
    assert sorted(ups["wave2_modules"]) == sorted(exp_w2)
    assert ups["active_modules"] == active


# -- v3 test-loop step contract ------------------------------------------------

def test_parse_env_pairs():
    from infermatrix_copilot.engine.steps.rebase_v3 import _parse_env_pairs
    assert _parse_env_pairs("FOO=1 BAR=a=b") == {"FOO": "1", "BAR": "a=b"}
    assert _parse_env_pairs("") == {}
    assert _parse_env_pairs("NOEQ FOO=x") == {"FOO": "x"}


def test_v3_test_loop_step_contract(v3_env, settings, trace, monkeypatch):
    """The local loop excludes nightly jobs, passes each job's declared env
    pairs to the child, and runs the baseline with the worktree prepended
    to PYTHONPATH (main's files execute main's code)."""
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.step import FailureKind, StepContext
    from infermatrix_copilot.engine.step import StepResult
    from infermatrix_copilot.engine.steps import rebase_v3, \
        register_builtin_steps
    from infermatrix_copilot.rebase_engine import test_loop as tl_mod
    from infermatrix_copilot.testing import runner as runner_mod
    _, _, repo, run_dir = v3_env
    # no debug backend in this test regardless of the machine env
    monkeypatch.setattr(
        rebase_v3, "_tier_client",
        lambda ctx: StepResult(False, FailureKind.BLOCKED, "no backend"))
    calls = []

    def fake_run(self, job, env, *, baseline=False, dry_run=False):
        calls.append({"key": job.key, "job_env": dict(job.env),
                      "env": dict(env), "baseline": baseline})
        return runner_mod.TestOutcome(rc=0 if baseline else 1,
                                      log_file="")
    monkeypatch.setattr(runner_mod.TestRunner, "run", fake_run)
    wt = run_dir / "main_worktree"
    monkeypatch.setattr(tl_mod, "ensure_main_worktree",
                        lambda repo, path, base_ref="origin/main": wt)
    monkeypatch.setattr(tl_mod, "remove_main_worktree",
                        lambda repo, path: None)
    registry = register_builtin_steps(StepRegistry())
    ctx = StepContext(
        settings=settings, params={}, run_dir=run_dir, trace=trace,
        state={"task_spec": {"repo": "vllm-omni", "params": {}},
               "run_id": "run-t", "repo_path": str(repo)})
    r = asyncio.run(registry.get("rebase.v3_test_loop").handler(ctx))
    assert r.ok, r.summary
    # nightly excluded from the local loop
    assert {c["key"] for c in calls} == {"quick"}
    rebase_call = next(c for c in calls if not c["baseline"])
    baseline_call = next(c for c in calls if c["baseline"])
    # the job's declared env pairs reach the child
    assert rebase_call["job_env"] == {"QUICK_ENV": "1"}
    assert baseline_call["job_env"] == {"QUICK_ENV": "1"}
    # baseline PYTHONPATH prepends the worktree
    assert baseline_call["env"]["PYTHONPATH"].split(":")[0] == str(wt)
    assert rebase_call["env"].get("PYTHONPATH", "").split(":")[0] != str(wt)
    # rc=1 vs baseline rc=0 = regression; no debug backend -> failed
    data = Substate(run_dir, "run-t").read()
    assert data["tests"]["pipeline"]["failed_tests"] == ["quick"]


def test_v3_test_loop_empty_manifest_is_structural(v3_env, settings, trace,
                                                   tmp_path):
    """Zero runnable local jobs marks `manifest_empty` — the push gate
    blocks instead of sailing through a vacuous '0 failed'."""
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.step import StepContext
    from infermatrix_copilot.engine.steps import register_builtin_steps
    repo2 = tmp_path / "nightly-only"
    (repo2 / ".buildkite").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo2, check=True)
    (repo2 / ".buildkite" / "test-nightly.yml").write_text(yaml.safe_dump({
        "steps": [{"label": "Soak", "timeout_in_minutes": 1,
                   "commands": ["true"]}]}))
    registry = register_builtin_steps(StepRegistry())
    run_dir = tmp_path / "run-empty"
    run_dir.mkdir()
    ctx = StepContext(
        settings=settings, params={}, run_dir=run_dir, trace=trace,
        state={"task_spec": {"repo": "vllm-omni", "params": {}},
               "run_id": "run-e", "repo_path": str(repo2)})
    r = asyncio.run(registry.get("rebase.v3_test_loop").handler(ctx))
    assert r.ok and "manifest_empty" in r.summary
    sub = Substate(run_dir, "run-e").read()
    assert sub["manifest_empty"] is True
    assert not evaluate_push_gate(sub, {}).allowed


# -- v3 agent wiring -----------------------------------------------------------

@pytest.fixture()
def v3_agent_env(v3_env, settings):
    """v3_env plus the real adapter rebase/ data (templates, tool schemas,
    hooks) so agent-assembly paths load for real."""
    import shutil
    adir = Path(settings.adapters_dir) / "vllm_omni"
    shutil.copytree(REPO_ROOT / "adapters" / "vllm_omni" / "rebase",
                    adir / "rebase")
    return v3_env


def test_v3_debug_fn_invokes_agent_and_verifies(v3_agent_env, settings,
                                                trace, monkeypatch):
    """The regression debug_fn actually invokes the configured agent
    backend (require_plan_review off, debug prompt) and only a green
    RE-RUN counts as fixed."""
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.step import StepContext
    from infermatrix_copilot.engine.steps import rebase_v3, \
        register_builtin_steps
    from infermatrix_copilot.rebase_engine import agent_loop as al
    from infermatrix_copilot.rebase_engine import test_loop as tl_mod
    from infermatrix_copilot.testing import runner as runner_mod
    _, _, repo, run_dir = v3_agent_env
    monkeypatch.setattr(
        rebase_v3, "_tier_client",
        lambda ctx: (object(), SimpleNamespace(
            model="m-test", api_key="k", base_url="", source="tier:eco")))
    agent_calls = []

    async def fake_loop(client, prompt, **kw):
        agent_calls.append(kw)
        return {"done": True, "text": "fixed", "turns": 2}
    monkeypatch.setattr(al, "run_agent_loop", fake_loop)

    runs = {"quick": 0}

    def fake_run(self, job, env, *, baseline=False, dry_run=False):
        if baseline:
            return runner_mod.TestOutcome(rc=0)
        runs[job.key] += 1
        # first rebase run fails; the post-debug re-run passes
        return runner_mod.TestOutcome(rc=1 if runs[job.key] == 1 else 0)
    monkeypatch.setattr(runner_mod.TestRunner, "run", fake_run)
    monkeypatch.setattr(tl_mod, "ensure_main_worktree",
                        lambda repo, path, base_ref="origin/main":
                        run_dir / "wt")
    monkeypatch.setattr(tl_mod, "remove_main_worktree",
                        lambda repo, path: None)
    registry = register_builtin_steps(StepRegistry())
    ctx = StepContext(
        settings=settings, params={}, run_dir=run_dir, trace=trace,
        state={"task_spec": {"repo": "vllm-omni", "params": {}},
               "run_id": "run-d", "repo_path": str(repo)})
    r = asyncio.run(registry.get("rebase.v3_test_loop").handler(ctx))
    assert r.ok, r.summary
    assert len(agent_calls) == 1
    assert agent_calls[0]["require_plan_review"] is False
    assert agent_calls[0]["scope"] is not None       # C5: debug is scoped too
    assert runs["quick"] == 2                        # verified by re-run
    data = Substate(run_dir, "run-d").read()
    assert data["tests"]["pipeline"]["failed_tests"] == []
    assert data["tests"]["pipeline"]["passed"] == 1


def test_v3_module_scope_and_serialization(v3_agent_env, settings, trace,
                                           monkeypatch):
    """C5: every module agent gets a ToolScope — repo tree as the writable
    wall, manifest local_paths as primary. Fan-out siblings SERIALIZE (they
    mutate the same checkout)."""
    from infermatrix_copilot.engine.registry import StepRegistry
    from infermatrix_copilot.engine.step import StepContext
    from infermatrix_copilot.engine.steps import rebase_v3, \
        register_builtin_steps
    from infermatrix_copilot.rebase_engine import module_rebase as mr
    _, _, repo, run_dir = v3_agent_env
    monkeypatch.setattr(
        rebase_v3, "_tier_client",
        lambda ctx: (object(), SimpleNamespace(
            model="m-test", api_key="k", base_url="", source="tier:eco")))
    events, scopes = [], {}

    async def fake_rebase_module(module, **kw):
        scopes[module] = kw.get("scope")
        events.append(("enter", module))
        await asyncio.sleep(0.02)
        events.append(("exit", module))
        return {"status": "done", "exit_code": 0, "debug_attempts": 0,
                "turns": 1, "summary": ""}
    monkeypatch.setattr(mr, "rebase_module", fake_rebase_module)
    registry = register_builtin_steps(StepRegistry())
    handler = registry.get("rebase.v3_module_rebase").handler

    def ctx_for(item):
        return StepContext(
            settings=settings, params={}, run_dir=run_dir, trace=trace,
            item=item,
            state={"task_spec": {"repo": "vllm-omni", "params": {}},
                   "run_id": "run-m", "repo_path": str(repo)})

    async def both():
        return await asyncio.gather(
            handler(ctx_for("worker_runner")),
            handler(ctx_for("model_executor")))
    r1, r2 = asyncio.run(both())
    assert r1.ok and r2.ok
    # serialized: no interleaving of enter/exit
    assert events[0][0] == "enter" and events[1] == ("exit", events[0][1])
    assert events[2][0] == "enter" and events[3] == ("exit", events[2][1])
    scope = scopes["worker_runner"]
    root = Path(str(repo)).resolve().as_posix()
    assert scope.name == "rebase-module:worker_runner"
    assert scope.path_scope.writable == (f"{root}/*",)
    assert any(p.startswith(f"{root}/vllm_omni/worker")
               for p in scope.path_scope.primary)
    assert scope.root == root
    # a write inside the repo but outside local_paths is out-of-scope
    d = scope.path_scope.check_write(f"{root}/vllm_omni/engine/core.py")
    assert d.allowed and d.out_of_scope
    assert not scope.path_scope.check_write("/etc/passwd").allowed


def test_v3_tier_client_pairs_endpoint_and_credential(trace, tmp_path,
                                                      monkeypatch):
    """The module/debug backend comes from `tier_target()` — model,
    endpoint, and credential resolved atomically (independent eco backend
    honored; no key ⇒ capability_gap BLOCKED)."""
    import anthropic
    from infermatrix_copilot.config import Settings
    from infermatrix_copilot.engine.step import StepResult
    from infermatrix_copilot.engine.steps.rebase_v3 import _tier_client
    captured = {}

    class FakeClient:
        def __init__(self, **kw):
            captured.update(kw)
    monkeypatch.setattr(anthropic, "AsyncAnthropic", FakeClient)
    s = Settings(_env_file=None, run_root=tmp_path / "runs",
                 eco_model="eco-m", eco_base_url="https://eco.example",
                 eco_api_key="eco-key", anthropic_api_key="global-key")
    ctx = SimpleNamespace(settings=s, trace=trace,
                          state={"task_spec": {"mode": "eco"}})
    client, target = _tier_client(ctx)
    assert isinstance(client, FakeClient)
    assert captured == {"api_key": "eco-key",
                        "base_url": "https://eco.example"}
    assert target.model == "eco-m" and target.source == "tier:eco"
    # no credential anywhere: BLOCKED with a declared capability_gap
    s2 = Settings(_env_file=None, run_root=tmp_path / "runs2",
                  anthropic_api_key="", eco_model="", eco_base_url="",
                  eco_api_key="")
    ctx2 = SimpleNamespace(settings=s2, trace=trace,
                           state={"task_spec": {"mode": "eco"}})
    r = _tier_client(ctx2)
    assert isinstance(r, StepResult) and not r.ok
