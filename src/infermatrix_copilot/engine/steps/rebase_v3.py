"""repo-rebase v3 steps — thin, governed wrappers over `rebase_engine`
(assembly PR; the playbook is CANDIDATE until the validation gate).

Every handler is substate-first (durable, run-stamped), publishes consumed
keys via `state_updates`, and fails typed — the transition-table terminal
rows are enforced by `rebase.v3_finalize` (all-steps-ok + substate failures
⇒ BLOCKED, the reused needs-human exit 3; it runs AFTER the report step so
RUN_REPORT always exists when the run terminates needs-human)."""

from __future__ import annotations

import asyncio
import shlex
from pathlib import Path

import yaml

from ...rebase_engine import test_loop as tl
from ...rebase_engine import wheel as wheel_mod
from ...rebase_engine.modes import MODES, MUTATING_MODES, mode_state_flags
from ...rebase_engine.phase1_steps import Phase1Config, run_commit_assignment
from ...rebase_engine.push_gate import evaluate_push_gate
from ...rebase_engine.substate import Substate
from ...rebase_engine.test_manifest import ManifestSpec, build_manifest
from ...rebase_engine.testing_env import scrubbed_agent_env
from ...scopes import PathScope, ToolScope
from ..step import FailureKind, StepContext, StepResult
from ._common import require_repo, step


def _task_params(ctx: StepContext) -> dict:
    spec = ctx.state.get("task_spec") or {}
    return (spec.get("params") if isinstance(spec, dict) else {}) or {}


def _adapter_manifest(ctx: StepContext) -> dict | StepResult:
    repo = (ctx.state.get("task_spec") or {}).get("repo", "")
    path = Path(ctx.settings.adapters_dir) / repo.replace("-", "_") / \
        "manifest.yaml"
    if not path.is_file():
        return StepResult(False, FailureKind.BLOCKED,
                          f"no adapter manifest for {repo!r} — the v3 "
                          "pipeline is adapter-data driven")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _substate(ctx: StepContext) -> Substate:
    return Substate(ctx.run_dir, ctx.state.get("run_id")
                    or ctx.run_dir.name)


def _parse_env_pairs(env_str: str) -> dict[str, str]:
    """The manifest job's `env` field ("K=V K2=V2", from stripped `export`
    lines) as a dict for `TestJob.env` — dropping a job's declared env would
    change what the test actually exercises."""
    out: dict[str, str] = {}
    try:
        parts = shlex.split(env_str or "")
    except ValueError:
        parts = (env_str or "").split()
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            if k:
                out[k] = v
    return out


def _tier_client(ctx: StepContext):
    """The run's agent backend via `Settings.tier_target` — the ONLY place a
    tier's model may pair with an endpoint and credential. Returns
    `(client, target)` or a BLOCKED StepResult (with a `capability_gap`
    trace) when no credential is configured for the resolved tier."""
    from ...config import TierNotConfiguredError
    mode = (ctx.state.get("task_spec") or {}).get("mode", "eco")
    try:
        target = ctx.settings.tier_target(mode)
    except TierNotConfiguredError as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    if not target.api_key:
        ctx.trace.record("capability_gap", capability="rebase.module_agent",
                         detail=f"no API key for tier target {target.source} "
                                "— rebase agents cannot run")
        return StepResult(False, FailureKind.BLOCKED,
                          "rebase agents need a configured Anthropic-"
                          "compatible backend for the resolved tier")
    from anthropic import AsyncAnthropic
    kwargs: dict = {"api_key": target.api_key}
    if target.base_url:
        kwargs["base_url"] = target.base_url
    return AsyncAnthropic(**kwargs), target


def _module_scope(repo_root: str, module: str,
                  manifest: dict) -> ToolScope:
    """C5 path governance for one module agent: the repo tree is the hard
    writable wall; the module's manifest `local_paths` are its primary files
    — writes elsewhere in the tree execute but are RECORDED out-of-scope."""
    root = Path(repo_root).resolve()
    local = tuple(((manifest.get("modules") or {}).get(module) or {})
                  .get("local_paths") or ())
    return ToolScope(
        name=f"rebase-module:{module}",
        allowed_tools=frozenset(),  # extras bypass the builtin allowlist;
                                    # enforcement here is the path scope
        path_scope=PathScope(
            writable=(f"{root.as_posix()}/*",),
            primary=tuple(f"{(root / p).as_posix()}*" for p in local)),
        root=str(root))


# same-checkout module agents must never run concurrently — the executor's
# foreach fan-out gathers items, but every module mutates the SAME target
# tree (the parent runs wave members sequentially). One lock per run dir.
_MODULE_SERIAL: dict[str, asyncio.Lock] = {}


@step("rebase.v3_prelude", "deterministic", "read",
      "Validate mode + adapter data; init runtime, locks, and mode flags.")
async def _v3_prelude(ctx: StepContext) -> StepResult:
    """Publishes the `mode_*` flags every later `when:` gate uses (Rev 8
    §2.1 — the mode was already resolved and written back by
    `resolve_effective_mode` before confirmation; an absent/unknown value
    here is a hard failure, not a default). For mutating modes it also
    initializes the run's world: the shared checkout flocks (released by a
    lifecycle finalizer on EVERY exit path), `upstream_path`, and the
    `last_rebase_upstream_commit` baseline (Rev 8 §3.4 — without these
    every full run would block at the wheel step and mutation paths would
    race external checkout users)."""
    mode = _task_params(ctx).get("rebase_mode", "")
    if mode not in MODES:
        return StepResult(False, FailureKind.BLOCKED,
                          f"rebase_mode missing/unknown ({mode!r}) — "
                          "resolve_effective_mode did not run; refuse to "
                          "guess permissions")
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    if manifest.get("status") != "active":
        return StepResult(False, FailureKind.BLOCKED,
                          "adapter is not active — v3 refuses inactive "
                          "adapters")

    updates: dict = {}
    from ...adapters.base import expand_path
    upstream = ctx.state.get("upstream_path", "") or expand_path(
        (manifest.get("upstream") or {}).get("repo_path", ""))
    if upstream:
        updates["upstream_path"] = upstream
    baseline = _task_params(ctx).get("last_rebase_commit", "") \
        or ctx.state.get("last_rebase_upstream_commit", "")
    if baseline:
        updates["last_rebase_upstream_commit"] = baseline
    if mode == "full":
        if not upstream:
            return StepResult(False, FailureKind.BLOCKED,
                              "full mode needs the upstream checkout — set "
                              "the manifest upstream.repo_path (env var "
                              "unset?)")
        if not baseline:
            return StepResult(False, FailureKind.BLOCKED,
                              "full mode needs the last-rebase baseline — "
                              "pass --task-param last_rebase_commit=<sha>")

    if mode in MUTATING_MODES:
        repo = require_repo(ctx)
        if isinstance(repo, StepResult):
            return repo
        from ...rebase_engine.runctx import CheckoutLock
        rb = manifest.get("rebase") or {}
        locks = [CheckoutLock(Path(repo), rb.get("lock_name", "checkout"))]
        if upstream and mode == "full":
            locks.append(CheckoutLock(Path(upstream), "upstream"))
        held: list = []
        for lock in locks:
            if not lock.acquire(blocking=False):
                for h in held:
                    h.release()
                return StepResult(False, FailureKind.BLOCKED,
                                  f"another run holds {lock.path} — an "
                                  "external or archival run is active on "
                                  "this checkout")
            held.append(lock)
        from ..lifecycle import register_finalizer

        async def _release_locks(_outcome, _held=tuple(held)) -> None:
            for h in _held:
                h.release()

        register_finalizer(ctx.run_dir, _release_locks)
        ctx.trace.record("checkout_locks_acquired",
                         paths=[str(lk.path) for lk in held])

    sub = _substate(ctx)
    sub.update({"phase": "init", **{k: v for k, v in
                                    mode_state_flags(mode).items()}})
    return StepResult(True, summary=f"mode={mode}",
                      outputs={"state_updates": {
                          **mode_state_flags(mode), **updates,
                          "run_id": sub.run_id}})


@step("rebase.v3_scan", "deterministic", "read",
      "Report-only scan: manifest + drift preview, stores untouched.")
async def _v3_scan(ctx: StepContext) -> StepResult:
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    spec = ManifestSpec.from_manifest(manifest)
    built = build_manifest(Path(repo), spec)
    out = ctx.run_dir / "test_manifest.json"
    import json
    out.write_text(json.dumps(built.to_dict(), indent=1), encoding="utf-8")
    return StepResult(True,
                      summary=f"{len(built.jobs)} CI jobs, "
                              f"{len(built.changes)} test changes",
                      outputs={"state_updates": {
                          "manifest_jobs": len(built.jobs)}})


@step("rebase.v3_wheel", "deterministic", "write_workspace",
      "Pick the wheel commit and pin the CI Dockerfile.")
async def _v3_wheel(ctx: StepContext) -> StepResult:
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    rb = manifest.get("rebase") or {}
    wheel_spec = wheel_mod.WheelSpec.from_manifest(rb["wheel"])
    pin = wheel_mod.PinSpec.from_manifest(rb["wheel"]["pin"])
    upstream = ctx.state.get("upstream_path", "")
    if not upstream:
        return StepResult(False, FailureKind.BLOCKED,
                          "upstream_path not in state — prelude/config gap")
    branch = (manifest.get("upstream") or {}).get("target_branch") \
        or (manifest.get("repo") or {}).get("default_branch", "main")
    try:
        found = wheel_mod.pick_wheel_commit(
            Path(upstream), branch, wheel_spec,
            probe=wheel_mod.make_arch_probe(wheel_spec),
            baseline=ctx.state.get("last_rebase_upstream_commit", ""),
            force_commit=_task_params(ctx).get("force_upstream_commit", ""))
        wheel_mod.pin_dockerfile(Path(repo), found, pin)
    except wheel_mod.WheelPickError as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    except wheel_mod.PinError as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    _substate(ctx).set_field("upstream_commit", found)
    return StepResult(True, summary=f"wheel commit {found[:12]}",
                      outputs={"state_updates": {"upstream_commit": found}})


@step("rebase.v3_assign", "deterministic", "read",
      "Classify upstream commits into modules; publish the wave lists.")
async def _v3_assign(ctx: StepContext) -> StepResult:
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    upstream = ctx.state.get("upstream_path", "")
    baseline = ctx.state.get("last_rebase_upstream_commit", "")
    if not upstream or not baseline:
        return StepResult(False, FailureKind.BLOCKED,
                          "upstream_path/baseline not in state")
    cfg = Phase1Config(
        upstream_repo=Path(upstream), target_repo=Path("."),
        log_dir=ctx.run_dir, baseline_commit=baseline,
        base_class_watch_paths=tuple((manifest.get("rebase") or {})
                                     .get("base_class_watch_paths") or ()))
    modules = manifest.get("modules") or {}
    module_paths = {m: tuple((s or {}).get("upstream_paths") or ())
                    for m, s in modules.items()}
    from ...rebase_engine.assign import AssignError
    try:
        result = run_commit_assignment(cfg, module_paths, _substate(ctx))
    except AssignError as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    active = [m for m, s in result.skip.items() if not s]
    # wave ordering is a dependency contract (manifest `wave`, parent
    # parity): wave 1 runs first; the wave gate empties wave 2 on failure
    wave1 = [m for m in modules if m in active
             and int((modules[m] or {}).get("wave") or 2) == 1]
    wave2 = [m for m in modules if m in active and m not in wave1]
    return StepResult(True,
                      summary=f"{result.total_commits} commits over "
                              f"{len(active)} active modules "
                              f"(wave1={len(wave1)}, wave2={len(wave2)})",
                      outputs={"state_updates": {
                          "active_modules": active,
                          "wave1_modules": wave1,
                          "wave2_modules": wave2}})


@step("rebase.v3_wave_gate", "deterministic", "read",
      "Wave gate: a wave-1 failure empties wave 2 (or ESCALATEs on halt).")
async def _v3_wave_gate(ctx: StepContext) -> StepResult:
    """Rev 8 §2.2: the gate ALWAYS runs between the waves. Any wave-1
    module failure empties `wave2_modules` (dependents must not build on a
    broken base); `halt_on_module_failure=true` escalates instead."""
    sub = _substate(ctx)
    data = sub.read()
    wave1 = ctx.state.get("wave1_modules") or []
    failed = [m for m in wave1
              if ((data.get("modules") or {}).get(m) or {})
              .get("status") == "failed"]
    if not failed:
        return StepResult(True, summary="wave 1 clean; wave 2 proceeds")
    if _task_params(ctx).get("halt_on_module_failure"):
        return StepResult(False, FailureKind.ESCALATE,
                          "halt_on_module_failure: wave-1 module(s) failed: "
                          + ", ".join(failed))
    ctx.trace.record("wave_gate", failed_wave1=failed, wave2_emptied=True)
    return StepResult(True,
                      summary=f"wave-1 failure(s) ({', '.join(failed)}) — "
                              "wave 2 emptied",
                      outputs={"state_updates": {"wave2_modules": []}})


async def _run_debug_agent(ctx: StepContext, manifest: dict, module: str,
                           slug: str, traceback_text: str) -> bool:
    """One regression-debug agent attempt for a failing test's module —
    the configured state-injected backend the loop's `debug_fn` invokes.
    Returns True when the agent claims completion (the caller re-runs the
    test; only a green re-run counts as fixed)."""
    client = _tier_client(ctx)
    if isinstance(client, StepResult):
        return False
    client, target = client
    from ...rebase_engine.agent_loop import run_agent_loop
    from ...rebase_engine.prompt_builder import (ModulePromptData,
                                                 build_debug_prompt)
    from ...rebase_engine.rebase_tools import (RebaseBackends, RebasePaths,
                                               build_rebase_tools,
                                               load_tool_schemas)
    repo_name = (ctx.state.get("task_spec") or {}).get("repo", "")
    adapter_dir = Path(ctx.settings.adapters_dir) / repo_name.replace("-", "_")
    data = ModulePromptData.load(adapter_dir / "rebase")
    defs = load_tool_schemas(adapter_dir / "rebase" / "tool_schemas.json")
    repo_root = ctx.state.get("repo_path", "")
    paths = RebasePaths(omni_path=repo_root,
                        vllm_path=ctx.state.get("upstream_path", ""),
                        env=scrubbed_agent_env())
    tools = build_rebase_tools(defs, paths, RebaseBackends())
    prompt = build_debug_prompt(module or slug, traceback_text,
                                data.debug_prompt_template, slug)
    agent_log = ctx.run_dir / "agents" / f"debug-{slug}.log"
    agent_log.parent.mkdir(parents=True, exist_ok=True)
    ctx.trace.record("debug_attempt", slug=slug, module=module,
                     model=target.model)
    try:
        result = await run_agent_loop(
            client, prompt, model=target.model, tool_defs=defs,
            extra_tools=tools,
            scope=_module_scope(repo_root, module or slug, manifest),
            trace=ctx.trace, require_plan_review=False,
            agent_log=str(agent_log))
    except Exception as exc:  # noqa: BLE001 - a debug crash is "not fixed"
        ctx.trace.record("debug_attempt_error", slug=slug, error=str(exc))
        return False
    return bool(result.get("done"))


@step("rebase.v3_test_loop", "script", "write_workspace",
      "The local test loop: run, baseline-compare, debug regressions.")
async def _v3_test_loop(ctx: StepContext) -> StepResult:
    """Runs the manifest jobs through the PR1 runner with main-baseline
    comparison. Local-loop contract (parent parity): nightly-sourced jobs
    are excluded; job env pairs reach the child; the baseline run prepends
    the worktree to PYTHONPATH so main's files execute against main's code;
    timeouts/watchdog kills are recorded as INFRASTRUCTURE failures
    (structural for the push gate, never assertion pass-through); an empty
    manifest marks `manifest_empty` instead of vacuously passing. The
    regression DEBUG agent runs on the tier backend — absent one,
    regressions are recorded as failures with a declared `capability_gap`
    (fail closed, never silently skipped)."""
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    spec = ManifestSpec.from_manifest(manifest)
    built = build_manifest(Path(repo), spec)
    sub = _substate(ctx)

    jobs = built.to_dict()["jobs"]
    local_jobs = [j for j in jobs if j.get("source") != "nightly"]
    if len(local_jobs) < len(jobs):
        ctx.trace.record("nightly_jobs_excluded",
                         count=len(jobs) - len(local_jobs))
    if not local_jobs:
        # zero runnable jobs is corrupt/empty manifest territory — the push
        # gate must block, not sail through a vacuous "0 failed"
        sub.update({"manifest_empty": True,
                    "tests": {"pipeline": {"passed": 0, "failed": 0,
                                           "failed_tests": [],
                                           "skipped": 0}}})
        return StepResult(True,
                          summary="no runnable local jobs — manifest_empty "
                                  "set (push gate blocks)",
                          outputs={"state_updates": {"phase3_failed": []}})

    from ...testing.env_plan import build_subprocess_env
    from ...testing.runner import TestJob, TestRunner
    from ...testing.watchdog import WatchdogPatterns
    rb = manifest.get("rebase") or {}
    adapter_dir = Path(ctx.settings.adapters_dir) / \
        ((ctx.state.get("task_spec") or {}).get("repo", "")).replace("-", "_")
    pat_file = adapter_dir / "testing" / "watchdog_patterns.yaml"
    patterns = WatchdogPatterns.from_yaml(pat_file) \
        if pat_file.is_file() else None
    runner = TestRunner(
        repo_root=Path(repo), tests_dir=ctx.run_dir / "tests",
        patterns=patterns, gpu_lock_dir=ctx.run_dir / "gpu_lock",
        artifact_globs=list((rb.get("testing") or {})
                            .get("artifact_globs") or []),
        cuda_visible_devices=str(
            scrubbed_agent_env().get("CUDA_VISIBLE_DEVICES", "")))
    jobs_by_slug = {j["slug"]: j for j in local_jobs}

    def _job(slug: str) -> TestJob:
        j = jobs_by_slug[slug]
        return TestJob(key=j["slug"], command=j["command"],
                       timeout_sec=j["timeout_sec"], min_gpus=j["min_gpus"],
                       env=_parse_env_pairs(j.get("env", "")))

    def run_fn(slug: str) -> tl.TestRunResult:
        outcome = runner.run(_job(slug), scrubbed_agent_env())
        infra = "timeout" if outcome.timed_out else \
            ("watchdog kill" if outcome.watchdog_triggered else "")
        return tl.TestRunResult(rc=outcome.rc, skipped=outcome.skipped,
                                skip_reason=outcome.skip_reason,
                                output=outcome.log_file, infra=infra)

    worktree_path = ctx.run_dir / "main_worktree"

    def baseline_fn(slug: str) -> tl.TestRunResult | None:
        wt = tl.ensure_main_worktree(Path(repo), worktree_path)
        if wt is None:
            return None
        wt_runner = TestRunner(
            repo_root=wt, tests_dir=ctx.run_dir / "tests",
            patterns=patterns, gpu_lock_dir=ctx.run_dir / "gpu_lock",
            cuda_visible_devices=runner.cuda)
        # main's files must import main's code: prepend the worktree so the
        # baseline never executes against rebase dependencies (parent's
        # baseline PYTHONPATH override)
        env = build_subprocess_env(base=scrubbed_agent_env(),
                                   pythonpath_prepend=str(wt))
        outcome = wt_runner.run(_job(slug), env, baseline=True)
        return tl.TestRunResult(rc=outcome.rc, skipped=outcome.skipped)

    async def debug_fn(slug: str, label: str, rc: int, output: str) -> bool:
        tier = _tier_client(ctx)
        if isinstance(tier, StepResult):
            ctx.trace.record("capability_gap",
                             capability="rebase.debug_agent",
                             detail=f"no agent backend; {slug} regression "
                                    "recorded as failed")
            return False
        traceback_text = ""
        try:
            log_path = Path(output)
            if log_path.is_file():
                traceback_text = "\n".join(
                    log_path.read_text(encoding="utf-8",
                                       errors="replace")
                    .splitlines()[-200:])
        except OSError:
            pass
        attempted = await _run_debug_agent(
            ctx, manifest, jobs_by_slug[slug].get("module", ""), slug,
            traceback_text or f"{label} failed with rc={rc}")
        if not attempted:
            return False
        rerun = run_fn(slug)  # only a green re-run counts as fixed
        return rerun.rc == 0 and not rerun.skipped and not rerun.infra

    result = await tl.run_test_loop(
        local_jobs, substate=sub, run_fn=run_fn,
        baseline_fn=baseline_fn, debug_fn=debug_fn,
        visible_gpus=len([d for d in runner.cuda.split(",") if d.strip()
                          and not d.strip().startswith("-")]))
    tl.remove_main_worktree(Path(repo), worktree_path)
    sub.update({"tests": {
        "pipeline": {
            "passed": result["passed"], "failed": result["failed"],
            "failed_tests": result["failed_tests"],
            "skipped": len(result["skipped_tests"])},
        "infra_failures": result["infra_failures"]}})
    return StepResult(True,
                      summary=f"{result['passed']} passed, "
                              f"{result['failed']} failed "
                              f"({len(result['infra_failures'])} infra), "
                              f"{len(result['skipped_tests'])} skipped",
                      outputs={"state_updates": {
                          "phase3_failed": result["failed_tests"]}})


@step("rebase.v3_push_gate", "deterministic", "read",
      "Fail-closed push gate: structural failures block; assertions flag.")
async def _v3_push_gate(ctx: StepContext) -> StepResult:
    from ...rebase_engine.modes import ModeConflictError
    sub = _substate(ctx)
    try:
        decision = evaluate_push_gate(sub.read(), _task_params(ctx))
    except ModeConflictError as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    if not decision.allowed:
        return StepResult(False, FailureKind.FORBIDDEN,
                          "push gate: " + "; ".join(decision.reasons))
    summary = "push gate open"
    if decision.flagged:
        summary += f" ({len(decision.flagged)} flagged test failure(s))"
    return StepResult(True, summary=summary,
                      outputs={"state_updates": {
                          "push_gate_flagged": list(decision.flagged)}})


@step("rebase.v3_finalize", "deterministic", "read",
      "Transition-table terminal row: substate failures ⇒ needs-human.")
async def _v3_finalize(ctx: StepContext) -> StepResult:
    """Rev 8 §3.1 row 2: all steps ok but substate carries failed
    modules/tests ⇒ the run terminates needs-human via the REUSED blocked /
    exit-3 semantics (Decision 4 — no new exit code). Runs AFTER the report
    step, so RUN_REPORT exists and the BLOCKED outcome only adds the
    ESCALATION artifact. The finalizer never upgrades a failure into
    success; substate `phase` records the honest terminal name."""
    sub = _substate(ctx)
    data = sub.read()
    failures: list[str] = []
    for module, spec in (data.get("modules") or {}).items():
        if (spec or {}).get("status") == "failed":
            failures.append(f"module {module}")
    tests = data.get("tests") or {}
    failed_tests = ((tests.get("pipeline") or {}).get("failed_tests")) or []
    failures.extend(f"test {t}" for t in failed_tests)
    failures.extend(f"infra {i}" for i in tests.get("infra_failures") or [])
    if data.get("manifest_empty"):
        failures.append("manifest empty")
    sub.update({"phase": "needs_human" if failures else "done"})
    if failures:
        return StepResult(False, FailureKind.BLOCKED,
                          "completed with failures needing a human: "
                          + "; ".join(failures[:10]))
    return StepResult(True, summary="substate clean; phase=done")


@step("rebase.v3_module_rebase", "script", "write_workspace",
      "One module's rebase agent (foreach over the wave lists).")
async def _v3_module_rebase(ctx: StepContext) -> StepResult:
    """The PR4a/PR4b assembly: golden-parity prompt → gated loop → substate
    outcome, per module via foreach fan-out. Fan-out siblings SERIALIZE on a
    per-run lock (they all mutate the same checkout; the parent runs wave
    members sequentially). Requires the tier-resolved backend; absent one
    this BLOCKS with a declared capability_gap (never a silent skip). Module
    failures are substate data (the wave gate and the finalize row consume
    them), so the step itself returns ok."""
    module = str(ctx.item or "")
    if not module:
        return StepResult(False, FailureKind.BLOCKED,
                          "v3_module_rebase needs a foreach module item")
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    client = _tier_client(ctx)
    if isinstance(client, StepResult):
        return client
    client, target = client
    from ...rebase_engine.hooks import load_hooks
    from ...rebase_engine.module_rebase import ModuleRunConfig, rebase_module
    from ...rebase_engine.prompt_builder import ModulePromptData
    from ...rebase_engine.rebase_tools import (RebaseBackends, RebasePaths,
                                               build_rebase_tools,
                                               load_tool_schemas)
    repo_name = (ctx.state.get("task_spec") or {}).get("repo", "")
    adapter_dir = Path(ctx.settings.adapters_dir) / repo_name.replace("-", "_")
    data = ModulePromptData.load(adapter_dir / "rebase")
    defs = load_tool_schemas(adapter_dir / "rebase" / "tool_schemas.json")
    repo_root = ctx.state.get("repo_path", "")
    paths = RebasePaths(omni_path=repo_root,
                        vllm_path=ctx.state.get("upstream_path", ""),
                        env=scrubbed_agent_env())
    tools = build_rebase_tools(defs, paths, RebaseBackends())
    hooks = load_hooks(adapter_dir, manifest)
    config = ModuleRunConfig(
        vllm_path=paths.vllm_path, omni_path=paths.omni_path,
        script_dir=str(adapter_dir / "rebase"), model=target.model,
        log_dir=str(ctx.run_dir),
        last_rebase_vllm_commit=ctx.state.get("last_rebase_upstream_commit",
                                              ""))
    serial = _MODULE_SERIAL.setdefault(str(ctx.run_dir), asyncio.Lock())
    async with serial:
        outcome = await rebase_module(
            module, client=client, config=config,
            prompt_data=data, tool_defs=defs, extra_tools=tools,
            substate=_substate(ctx), hooks=hooks,
            scope=_module_scope(repo_root, module, manifest),
            trace=ctx.trace)
    return StepResult(True,
                      summary=f"{module}: {outcome['status']} "
                              f"(debug_attempts={outcome['debug_attempts']})",
                      outputs={"state_updates": {
                          f"module_{module}_status": outcome["status"]}})


@step("rebase.v3_ci", "script", "push",
      "Remote CI: push, guarded build creation, monitored to terminal.")
async def _v3_ci(ctx: StepContext) -> StepResult:
    """remote_ci/full phase 4: commit-and-push through the PR3 cluster (C4
    double gate inside), then a guarded op-recorded build monitored to a
    terminal state. Requires the CI provider client — absent a token this
    BLOCKS with a declared capability_gap."""
    if not getattr(ctx.settings, "buildkite_api_token", ""):
        ctx.trace.record("capability_gap", capability="ci.provider_client",
                         detail="no CI token — remote CI cannot run")
        return StepResult(False, FailureKind.BLOCKED,
                          "remote CI needs a provider token; run local_ci "
                          "instead")
    return StepResult(False, FailureKind.BLOCKED,
                      "the provider HTTP client lands with the live-run "
                      "wiring (EXT1/PR6 preflight); use local_ci until then")
