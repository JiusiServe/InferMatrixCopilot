"""repo-rebase v3 steps — thin, governed wrappers over `rebase_engine`
(assembly PR; the playbook is CANDIDATE until the validation gate).

Every handler is substate-first (durable, run-stamped), publishes consumed
keys via `state_updates`, and fails typed — the transition-table terminal
rows are enforced by `rebase.v3_finalize` (all-steps-ok + substate failures
⇒ BLOCKED, the reused needs-human exit 3)."""

from __future__ import annotations

from pathlib import Path

import yaml

from ...rebase_engine import test_loop as tl
from ...rebase_engine import wheel as wheel_mod
from ...rebase_engine.modes import MODES, mode_state_flags
from ...rebase_engine.phase1_steps import Phase1Config, run_commit_assignment
from ...rebase_engine.push_gate import evaluate_push_gate
from ...rebase_engine.substate import Substate
from ...rebase_engine.test_manifest import ManifestSpec, build_manifest
from ...rebase_engine.testing_env import scrubbed_agent_env
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


@step("rebase.v3_prelude", "deterministic", "read",
      "Validate mode + adapter data; seed mode flags and substate.")
async def _v3_prelude(ctx: StepContext) -> StepResult:
    """Publishes the `mode_*` flags every later `when:` gate uses (Rev 8
    §2.1 — the mode was already resolved and written back by
    `resolve_effective_mode` before confirmation; an absent/unknown value
    here is a hard failure, not a default)."""
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
    sub = _substate(ctx)
    sub.update({"phase": "init", **{k: v for k, v in
                                    mode_state_flags(mode).items()}})
    return StepResult(True, summary=f"mode={mode}",
                      outputs={"state_updates": {
                          **mode_state_flags(mode),
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
      "Classify upstream commits into modules; skip flags into substate.")
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
    module_paths = {m: tuple((s or {}).get("upstream_paths") or ())
                    for m, s in (manifest.get("modules") or {}).items()}
    from ...rebase_engine.assign import AssignError
    try:
        result = run_commit_assignment(cfg, module_paths, _substate(ctx))
    except AssignError as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    return StepResult(True,
                      summary=f"{result.total_commits} commits over "
                              f"{sum(1 for s in result.skip.values() if not s)}"
                              " active modules",
                      outputs={"state_updates": {
                          "active_modules": [m for m, s in result.skip.items()
                                             if not s]}})


@step("rebase.v3_test_loop", "script", "write_workspace",
      "The local test loop: run, baseline-compare, debug regressions.")
async def _v3_test_loop(ctx: StepContext) -> StepResult:
    """Runs the manifest jobs through the PR1 runner with main-baseline
    comparison. The regression DEBUG agent requires the run's LLM client —
    absent one, regressions are recorded as failures with a declared
    `capability_gap` (fail closed, never silently skipped)."""
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    spec = ManifestSpec.from_manifest(manifest)
    built = build_manifest(Path(repo), spec)
    sub = _substate(ctx)

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
    jobs_by_slug = {j.slug: j for j in built.jobs}

    def run_fn(slug: str) -> tl.TestRunResult:
        j = jobs_by_slug[slug]
        env = scrubbed_agent_env()
        outcome = runner.run(TestJob(key=j.slug, command=j.command,
                                     timeout_sec=j.timeout_sec,
                                     min_gpus=j.min_gpus), env)
        return tl.TestRunResult(rc=outcome.rc, skipped=outcome.skipped,
                                skip_reason=outcome.skip_reason,
                                output=outcome.log_file)

    worktree_path = ctx.run_dir / "main_worktree"

    def baseline_fn(slug: str) -> tl.TestRunResult | None:
        wt = tl.ensure_main_worktree(Path(repo), worktree_path)
        if wt is None:
            return None
        j = jobs_by_slug[slug]
        wt_runner = TestRunner(
            repo_root=wt, tests_dir=ctx.run_dir / "tests",
            patterns=patterns, gpu_lock_dir=ctx.run_dir / "gpu_lock",
            cuda_visible_devices=runner.cuda)
        outcome = wt_runner.run(
            TestJob(key=j.slug, command=j.command,
                    timeout_sec=j.timeout_sec, min_gpus=j.min_gpus),
            scrubbed_agent_env(), baseline=True)
        return tl.TestRunResult(rc=outcome.rc, skipped=outcome.skipped)

    async def debug_fn(slug: str, label: str, rc: int, output: str) -> bool:
        if ctx.llm is None:
            ctx.trace.record("capability_gap",
                             capability="rebase.debug_agent",
                             detail=f"no LLM configured; {slug} regression "
                                    "recorded as failed")
            return False
        # the module debug agent (assembly of PR4a/PR4b pieces) is wired by
        # the caller through state; absent wiring fails closed
        ctx.trace.record("capability_gap",
                         capability="rebase.debug_agent",
                         detail="debug agent wiring arrives with the module "
                                "fan-out steps; regression recorded")
        return False

    result = await tl.run_test_loop(
        built.to_dict()["jobs"], substate=sub, run_fn=run_fn,
        baseline_fn=baseline_fn, debug_fn=debug_fn,
        visible_gpus=len([d for d in runner.cuda.split(",") if d.strip()
                          and not d.strip().startswith("-")]))
    tl.remove_main_worktree(Path(repo), worktree_path)
    sub.update({"tests": {"pipeline": {
        "passed": result["passed"], "failed": result["failed"],
        "failed_tests": result["failed_tests"],
        "skipped": len(result["skipped_tests"])}}})
    return StepResult(True,
                      summary=f"{result['passed']} passed, "
                              f"{result['failed']} failed, "
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
    exit-3 semantics (Decision 4 — no new exit code). The finalizer never
    upgrades a failure into success."""
    sub = _substate(ctx)
    data = sub.read()
    failures: list[str] = []
    for module, spec in (data.get("modules") or {}).items():
        if (spec or {}).get("status") == "failed":
            failures.append(f"module {module}")
    failed_tests = ((data.get("tests") or {}).get("pipeline") or {}) \
        .get("failed_tests") or []
    failures.extend(f"test {t}" for t in failed_tests)
    sub.update({"phase": "done"})
    if failures:
        return StepResult(False, FailureKind.BLOCKED,
                          "completed with failures needing a human: "
                          + "; ".join(failures[:10]))
    return StepResult(True, summary="substate clean; phase=done")


@step("rebase.v3_module_rebase", "script", "write_workspace",
      "One module's rebase agent (foreach over active_modules).")
async def _v3_module_rebase(ctx: StepContext) -> StepResult:
    """The PR4a/PR4b assembly: golden-parity prompt → gated loop → substate
    outcome, per module via foreach fan-out. Requires a configured LLM
    backend; absent one this BLOCKS with a declared capability_gap (never a
    silent skip). Module failures are substate data (wave gating and the
    finalize row consume them), so the step itself returns ok."""
    module = str(ctx.item or "")
    if not module:
        return StepResult(False, FailureKind.BLOCKED,
                          "v3_module_rebase needs a foreach module item")
    manifest = _adapter_manifest(ctx)
    if isinstance(manifest, StepResult):
        return manifest
    api_key = getattr(ctx.settings, "anthropic_api_key", "")
    if not api_key:
        ctx.trace.record("capability_gap", capability="rebase.module_agent",
                         detail="no ANTHROPIC_API_KEY — module agents "
                                "cannot run")
        return StepResult(False, FailureKind.BLOCKED,
                          "module agents need a configured Anthropic-"
                          "compatible backend")
    from anthropic import AsyncAnthropic
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
    paths = RebasePaths(omni_path=ctx.state.get("repo_path", ""),
                        vllm_path=ctx.state.get("upstream_path", ""),
                        env=scrubbed_agent_env())
    tools = build_rebase_tools(defs, paths, RebaseBackends())
    hooks = load_hooks(adapter_dir, manifest)
    tier = ctx.settings.tier_target(
        (ctx.state.get("task_spec") or {}).get("mode", "eco"))
    config = ModuleRunConfig(
        vllm_path=paths.vllm_path, omni_path=paths.omni_path,
        script_dir=str(adapter_dir / "rebase"), model=tier.model,
        log_dir=str(ctx.run_dir),
        last_rebase_vllm_commit=ctx.state.get("last_rebase_upstream_commit",
                                              ""))
    outcome = await rebase_module(
        module, client=AsyncAnthropic(api_key=api_key), config=config,
        prompt_data=data, tool_defs=defs, extra_tools=tools,
        substate=_substate(ctx), hooks=hooks, trace=ctx.trace)
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
