"""COMPLETE-RUN e2e for the v3 pipeline (post-PR5 gap: every earlier e2e
was a partial — the report-only path, or one cluster at a time).

Two complete runs through the REAL executor over the REAL playbook yaml:

* `local_ci` — a genuinely green end-to-end run to `done`: prelude
  (mode governance + prepared-tree precondition + checkout flock),
  self-cleaning guard with adapter policy, the manifest builder over a
  real nested pipeline, the REAL TestRunner executing real subprocesses,
  the real precommit step, report, finalize. Exit-0 semantics.

* `full` — the whole pipeline to its offline terminal: wheel pick over a
  real `git clone --shared` upstream scratch (probe faked — the only
  network piece), Dockerfile pin, commit assignment + waves (module agent
  faked at the `rebase_module` boundary — the only LLM piece; install
  faked — the only pip piece), real test loop, real precommit, real push
  gate, then the CI step BLOCKS on the declared provider-token capability
  gap (no BUILDKITE_API_TOKEN offline). Pins the §3.1 row-3 artifacts:
  the terminal-report finalizer writes RUN_REPORT.md, locks release, the
  scratch tears down.

* `remote_ci` — the wired phase 4 end to end (fake provider client, real
  everything else): real push over a real bare remote through the PR3
  cluster (WAL + absence-pinned lease), guarded op-recorded build, monitor
  to terminal, substate + finalize. Plus the ALLOW_PUSH-unset FORBIDDEN
  path and the ci-failed → needs-human terminal row.

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
    # no parent checkout in this fixture world; a declared knowledge layer
    # would (correctly) fail the prelude closed
    manifest["rebase"].pop("knowledge", None)
    # campaign pins name real upstream branches; the fixture upstream only
    # has its default branch
    (manifest.get("upstream") or {}).pop("target_branch", None)
    (adir / "manifest.yaml").write_text(yaml.safe_dump(manifest))
    shutil.copytree(REPO_ROOT / "adapters" / "vllm_omni" / "rebase",
                    adir / "rebase")
    settings.playbooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / "playbooks" / "repo-rebase-v3.yaml",
                settings.playbooks_dir / "repo-rebase-v3.yaml")

    # Deployment reality (live-launch finding 2026-08-23): adapter-declared
    # vars live in `.env` ONLY — never exported — so Settings.expansion_env
    # is the sole resolver. Exporting them here masked bare expand_path
    # call sites; the fixture now provides them the way production does.
    monkeypatch.delenv("VLLM_OMNI_VENV", raising=False)
    monkeypatch.delenv("VLLM_UPSTREAM_REPO", raising=False)
    base_expansion = type(settings).expansion_env
    monkeypatch.setattr(
        type(settings), "expansion_env",
        lambda self: {**base_expansion(self),
                      "VLLM_OMNI_VENV": str(tmp_path / "omni-venv"),
                      "VLLM_UPSTREAM_REPO": str(upstream)})
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
    """The COMPLETE full pipeline to its offline terminal: wheel pick over
    the real scratch clone + Dockerfile pin, real commit assignment, the
    wave fan-out (module agent faked at the rebase_module boundary), real
    tests + precommit + push gate — then the CI step BLOCKS on the
    declared provider-token capability gap (offline: no CI token). Pins
    §3.1 row 3: RUN_REPORT via the terminal-report finalizer, lock
    release, scratch teardown."""
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

    # offline terminal: BLOCKED at the CI step's token capability gap
    assert outcome.status == "blocked"
    assert "token" in outcome.blocked_reason.lower()
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


# ── remote_ci: the wired phase 4 ─────────────────────────────────────────────

class FakeBK:
    """Provider fake for the e2e: created builds pop scripted bodies;
    lookups are empty (no active siblings, no baseline builds)."""

    def __init__(self, bodies):
        self.bodies = list(bodies)
        self.builds: dict[str, dict] = {}
        self.created = 0

    def create_build(self, *, branch, commit, message, meta_data):
        self.created += 1
        bid = f"b{self.created}"
        body = self.bodies.pop(0)
        self.builds[bid] = {"id": bid, "web_url": f"u/{bid}",
                            "branch": branch, "commit": commit,
                            "meta_data": dict(meta_data), **body}
        return self.builds[bid]

    def get_build(self, build_id):
        return self.builds.get(build_id, {})

    def find_builds_by_meta(self, key, value):
        return [b for b in self.builds.values()
                if b["meta_data"].get(key) == value]

    def cancel_build(self, build_id):
        raise AssertionError("the run must never cancel builds")

    def get_job_log(self, build_id, job_id):
        return ""

    def list_jobs(self, build_id):
        return list(self.builds.get(build_id, {}).get("jobs") or [])

    def retry_job(self, build_id, job_id):
        return None, True

    def latest_builds(self, branch, states=(), per_page=30):
        return []

    def builds_for_commit(self, branch, commit):
        return []


def _wire_remote_ci(env, settings, tmp_path, monkeypatch, fake,
                    allow_push=True, branch="dev/vllm-align"):
    """Bare origin + the adapter-declared rebase branch + injected
    provider."""
    from infermatrix_copilot.engine.steps import rebase_v3
    remote = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
    subprocess.run(["git", "-C", env.repo, "remote", "add", "origin",
                    str(remote)], check=True)
    subprocess.run(["git", "-C", env.repo, "checkout", "-q", "-b",
                    branch], check=True)
    clients = []

    def factory(token, org, pipeline, build_env,
                ignore_branch_filters=False):
        clients.append((token, org, pipeline, dict(build_env)))
        return fake

    monkeypatch.setattr(rebase_v3, "_make_ci_client", factory)
    settings.buildkite_api_token = "tok"
    settings.allow_push = allow_push
    settings.rebase_ci_settle_sec = 0
    settings.rebase_ci_poll_sec = 0
    return remote, clients


def test_remote_ci_complete_run_green(complete_env, settings, tmp_path,
                                      monkeypatch):
    """A COMPLETE remote_ci run to `done`: prelude preconditions (pin +
    upstream-commit signal), real guard, vacuous push gate, a REAL push
    over a real bare remote through the PR3 cluster (WAL, absence-pinned
    lease), a guarded op-recorded build, monitor to terminal, substate,
    report, finalize."""
    env = complete_env
    fake = FakeBK([{"state": "passed", "jobs": [
        {"id": "j1", "name": "Unit Sweep", "state": "passed",
         "exit_status": 0}]}])
    remote, clients = _wire_remote_ci(env, settings, tmp_path, monkeypatch,
                                      fake)
    executor, run_dir = env.make_run("run-remoteci")
    state = _state_for(env, run_dir, {"rebase_mode": "remote_ci",
                                      "upstream_commit": "a" * 40})
    outcome = asyncio.run(executor.run(env.playbook, state))
    assert outcome.status == "done", getattr(outcome, "blocked_reason", "")
    data = Substate(run_dir, run_dir.name).read()
    assert data["ci"]["result"] == "passed"
    assert data["ci"]["rounds"][0]["purpose"] == "initial"
    assert data["phase"] == "done"
    # the push LANDED on the remote: HEAD == remote branch tip, WAL pushed
    head = subprocess.run(["git", "-C", env.repo, "rev-parse", "HEAD"],
                          capture_output=True, text=True,
                          check=True).stdout.strip()
    remote_tip = subprocess.run(
        ["git", "-C", remote, "rev-parse", "refs/heads/dev/vllm-align"],
        capture_output=True, text=True, check=True).stdout.strip()
    assert head == remote_tip
    from infermatrix_copilot.rebase_engine import ci_loop, push_wal
    recs = push_wal.load_records(run_dir / "push_wal")
    assert [(r.state, r.dest_ref) for r in recs] == \
        [("pushed", "refs/heads/dev/vllm-align")]
    # §3.2: the build is op-recorded and meta-stamped
    ops = ci_loop.load_ops(run_dir / "ci_ops")
    assert [(o.op_id, o.purpose, o.state) for o in ops] == \
        [(f"{run_dir.name}-ci-r0", "initial", "created")]
    assert fake.builds["b1"]["meta_data"] == {
        "imx_op_id": f"{run_dir.name}-ci-r0", "imx_run_id": run_dir.name}
    assert fake.builds["b1"]["commit"] == head
    # pipeline identities + trigger env came from the ADAPTER (build
    # client first, then the baseline-pipeline client)
    assert [(c[1], c[2]) for c in clients] == \
        [("vllm", "vllm-omni-release"), ("vllm", "vllm-omni-rebase")]
    assert clients[0][3] == {"NIGHTLY": "1", "RUN_HUNYUAN_IMAGE3_PERF": "1"}
    assert (run_dir / "RUN_REPORT.md").exists()
    asyncio.run(lifecycle.finalize(run_dir, outcome))
    probe = CheckoutLock(env.repo, "omni")
    assert probe.acquire(blocking=False) is True
    probe.release()


def test_remote_ci_requires_allow_push(complete_env, settings, tmp_path,
                                       monkeypatch):
    """§2.2: remote_ci without ALLOW_PUSH=1 is FORBIDDEN at phase 4 — the
    C4 env half is never self-granted; nothing reaches the remote or the
    provider."""
    env = complete_env
    fake = FakeBK([])
    remote, _ = _wire_remote_ci(env, settings, tmp_path, monkeypatch, fake,
                                allow_push=False)
    executor, run_dir = env.make_run("run-remoteci-dry")
    state = _state_for(env, run_dir, {"rebase_mode": "remote_ci",
                                      "upstream_commit": "a" * 40})
    outcome = asyncio.run(executor.run(env.playbook, state))
    assert outcome.status == "blocked"
    assert "ALLOW_PUSH" in outcome.blocked_reason
    assert fake.created == 0
    check = subprocess.run(
        ["git", "-C", remote, "rev-parse", "refs/heads/dev/vllm-align"],
        capture_output=True, text=True)
    assert check.returncode != 0        # nothing was pushed
    asyncio.run(lifecycle.finalize(run_dir, outcome))


def test_remote_ci_refuses_undeclared_branch(complete_env, settings,
                                             tmp_path, monkeypatch):
    """Round-1 review: push authorization is SCOPED to the adapter's
    declared `push.rebase_branch` — any other (even non-protected)
    checkout branch is FORBIDDEN before anything reaches the remote or
    the provider."""
    env = complete_env
    fake = FakeBK([])
    remote, _ = _wire_remote_ci(env, settings, tmp_path, monkeypatch, fake,
                                branch="dev/other-branch")
    executor, run_dir = env.make_run("run-remoteci-scope")
    state = _state_for(env, run_dir, {"rebase_mode": "remote_ci",
                                      "upstream_commit": "a" * 40})
    outcome = asyncio.run(executor.run(env.playbook, state))
    assert outcome.status == "blocked"
    assert "only the declared rebase branch" in outcome.blocked_reason
    assert "dev/vllm-align" in outcome.blocked_reason
    assert fake.created == 0
    assert subprocess.run(
        ["git", "-C", remote, "rev-parse", "refs/heads/dev/other-branch"],
        capture_output=True).returncode != 0
    asyncio.run(lifecycle.finalize(run_dir, outcome))


def test_remote_ci_failure_rules_needs_human(complete_env, settings,
                                             tmp_path, monkeypatch):
    """CI failures that survive debugging are SUBSTATE data (parent
    parity): the ci step itself is ok, the report is written, and the
    finalize terminal row rules needs-human (blocked / exit-3 semantics)
    naming the unfixed jobs."""
    env = complete_env
    from infermatrix_copilot.engine.steps import rebase_v3
    fake = FakeBK([{"state": "failed", "jobs": [
        {"id": "j1", "name": "Unit Sweep", "state": "failed",
         "exit_status": 1}]}])
    _wire_remote_ci(env, settings, tmp_path, monkeypatch, fake)

    async def no_fix(ctx, manifest, module, slug, tb):
        return "not_done"
    monkeypatch.setattr(rebase_v3, "_run_debug_agent", no_fix)
    executor, run_dir = env.make_run("run-remoteci-red")
    state = _state_for(env, run_dir, {"rebase_mode": "remote_ci",
                                      "upstream_commit": "a" * 40})
    outcome = asyncio.run(executor.run(env.playbook, state))
    assert outcome.status == "blocked"
    assert "remote CI failed" in outcome.blocked_reason
    assert "ci job Unit Sweep" in outcome.blocked_reason
    data = Substate(run_dir, run_dir.name).read()
    assert data["ci"]["result"] == "failed"
    assert data["ci"]["unfixed"] == ["Unit Sweep"]
    assert data["phase"] == "needs_human"
    # row 2 ordering: the report step ran BEFORE the terminal ruling
    assert (run_dir / "RUN_REPORT.md").exists()
    asyncio.run(lifecycle.finalize(run_dir, outcome))