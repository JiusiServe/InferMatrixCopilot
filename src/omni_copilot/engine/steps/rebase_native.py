"""Native repo-rebase steps: the 5-phase pipeline decomposed into copilot steps
by importing vllm-omni-rebase-agent's OWN functions (wrap, never reimplement).

Used by the `repo-rebase-native` playbook (status: candidate — the nightly
planner keeps recalling the locked delegating playbook until promotion).
Parent phase markers are still written via `agent.orchestrator._persist_state`
at the same points the parent orchestrator writes them, so falling back to
`omni-rebase-orchestrator --resume` stays possible after abandoning a copilot
run. All `agent.*` imports are lazy: ImportError -> BLOCKED.
"""

from __future__ import annotations

import os
from pathlib import Path

from ...rebase.monitor import parse_parent_state
from ..step import FailureKind, StepContext, StepResult, StepSpec
from ._common import register_step

# Memoized per-process parent runtime (env exported, stores initialized).
_RUNTIME: dict = {}


def _task_params(ctx: StepContext) -> dict:
    spec = ctx.state.get("task_spec") or {}
    return (spec.get("params") if isinstance(spec, dict) else {}) or {}


def _import_parent():
    """Lazy import of the parent package; None when not installed."""
    try:
        from agent import orchestrator as orch  # noqa: F401
        from agent.subgraphs import phase2 as p2  # noqa: F401
        return orch, p2
    except ImportError:
        return None, None


def _blocked_import() -> StepResult:
    return StepResult(False, FailureKind.BLOCKED,
                      "vllm-omni-rebase-agent is not importable — install it into "
                      "the same venv (pip install -e /rebase/vllm-omni-rebase-agent)")


def _ensure_runtime(ctx: StepContext) -> dict | StepResult:
    """Build (or rebuild after a process restart) the parent runtime: settings
    loaded, env exported, log dirs, stores initialized, RebaseState dict.
    Copilot progress.json stays the step-level source of truth; this makes the
    prelude idempotent per process so any later step can run after a resume."""
    want_run_id = ctx.state.get("rebase_run_id")
    if _RUNTIME and (_RUNTIME.get("run_id") == want_run_id or want_run_id is None):
        if ctx.state.get("rebase_state") is None:
            ctx.state["rebase_state"] = _RUNTIME["state"]
            ctx.state["rebase_run_id"] = _RUNTIME["run_id"]
        return _RUNTIME

    orch, _p2 = _import_parent()
    if orch is None:
        return _blocked_import()

    params = _task_params(ctx)
    argv: list[str] = []
    if params.get("local_ci_only"):
        argv.append("--local-ci-only")
    if params.get("remote_ci_only"):
        argv.append("--remote-ci-only")
    args = orch.parse_args(argv)
    settings = orch._load_settings(args)  # includes load_dotenv

    env_before = dict(os.environ)
    orch._export_all_settings(settings)
    os.environ["PROMPTS_PATH"] = str(Path(str(settings.prompts_path)).resolve())
    os.environ["BUILDKITE_API_TOKEN"] = settings.buildkite_api_token
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
    os.environ["TEST_TIMEOUT_SEC"] = "3600"
    env_delta = sorted(k for k, v in os.environ.items() if env_before.get(k) != v)
    ctx.trace.record("env_exported", added_or_changed=env_delta[:60],
                     count=len(env_delta))

    settings = orch.detect_baseline(settings)
    state = dict(orch.make_initial_state(settings))

    resuming = bool(ctx.state.get("resuming")) or want_run_id is not None
    if resuming:
        prev_run_id, prev_phase, prev_extra = orch._find_previous_run(settings)
        target = want_run_id or prev_run_id
        if prev_run_id and prev_run_id == target:
            state["run_id"] = prev_run_id
            state["phase"] = prev_phase or "init"
            if prev_extra:
                state["_resume_extra"] = prev_extra
                for k in ("main_ci_build_url", "main_ci_result",
                          "main_ci_failed_slugs", "main_ci_commit"):
                    if prev_extra.get(k):
                        state[k] = prev_extra[k]

    state["remote_ci_only_mode"] = bool(params.get("remote_ci_only"))
    state["local_ci_only_mode"] = bool(params.get("local_ci_only"))
    state["skip_rebase_mode"] = state["remote_ci_only_mode"] or state["local_ci_only_mode"]
    idx = params.get("main_ci_idx")
    if isinstance(idx, int) and idx > 0:
        state["main_ci_build_url"] = (
            "https://api.buildkite.com/v2/organizations/vllm/pipelines/"
            f"vllm-omni-rebase/builds/{idx}"
        )
    state["last_rebase_vllm_commit"] = settings.last_rebase_vllm_commit
    state["target_branch"] = settings.target_branch

    log_dir = orch._setup_log_dirs(settings, state["run_id"])

    from agent.debug_memory_store import init_store
    from agent.skills_store import init_skill_store

    root = Path(str(settings.prompts_path))
    init_store(db_path=str(root / "agent" / "store" / "debug_memory.db"),
               md_path=str(root / "agent" / "memory" / "debug_memory.md"))
    init_skill_store(str(root / "agent" / "skills"))
    os.environ["REBASE_RUN_ID"] = state["run_id"]
    head = orch._git_head_commit(str(settings.vllm_path))
    if head:
        os.environ["REBASE_VLLM_COMMIT"] = head

    _RUNTIME.clear()
    _RUNTIME.update({"run_id": state["run_id"], "settings": settings,
                     "state": state, "orch": orch, "log_dir": log_dir})
    ctx.state["rebase_state"] = state
    ctx.state["rebase_run_id"] = state["run_id"]
    ctx.state["parent_log_dir"] = str(log_dir)
    ctx.state["repo_path"] = str(settings.omni_path)
    return _RUNTIME


async def _prelude(ctx: StepContext) -> StepResult:
    orch, _ = _import_parent()
    if orch is None:
        return _blocked_import()

    state_file = Path(ctx.params.get("state_file")
                      or ctx.settings.rebase_agent_root / "rebase_logs" / "state.json")
    pre = parse_parent_state(state_file)
    resuming = bool(ctx.state.get("resuming"))
    if pre and pre.get("phase") not in ("", "done", None) and not resuming:
        return StepResult(False, FailureKind.BLOCKED,
                          f"parent state.json shows an in-flight run "
                          f"({pre.get('run_id')} at phase {pre.get('phase')}) — "
                          "resume it (/resume or omni-rebase-orchestrator --resume) "
                          "or clean it up before starting fresh")

    rt = _ensure_runtime(ctx)
    if isinstance(rt, StepResult):
        return rt
    settings = rt["settings"]

    # wave lists from the parent settings, minus already-done modules on resume
    done: set[str] = set()
    resume_extra = rt["state"].get("_resume_extra") or {}
    for m, info in (resume_extra.get("phase2_progress") or {}).get("modules", {}).items():
        if (info or {}).get("status") in ("done", "skipped"):
            done.add(m)
    wave1 = [m for m in settings.wave_1_modules if m not in done]
    wave2 = [m for m in settings.wave_2_modules if m not in done]
    ctx.state["wave1_modules"] = wave1
    ctx.state["wave2_modules"] = wave2

    # cross-check against plugin zero's module->wave map; drift is recorded
    try:
        from ...plugins.base import PluginRegistry
        plugin = PluginRegistry(ctx.settings.plugins_dir).resolve(name="vllm_omni")
        plugin_waves = {m: (s or {}).get("wave") for m, s in plugin.modules.items()}
        drift = [m for m in settings.wave_1_modules if plugin_waves.get(m) not in (1, None)]
        if drift:
            ctx.trace.record("wave_map_drift", modules=drift)
    except Exception:
        pass

    return StepResult(True,
                      summary=f"runtime ready (run {rt['run_id']}; wave1={wave1}, "
                              f"wave2={wave2})",
                      outputs={"run_id": rt["run_id"],
                               "state_updates": {
                                   "wave1_modules": wave1, "wave2_modules": wave2,
                                   "rebase_run_id": rt["run_id"],
                                   "parent_log_dir": str(rt["log_dir"]),
                               }})


def _phase_step(phase_module: str, wrapper_name: str, marker_after: str | None,
                skip_flag: str | None = None):
    """Factory for thin wrappers over the parent's phaseN_init_wrapper."""

    async def handler(ctx: StepContext) -> StepResult:
        rt = _ensure_runtime(ctx)
        if isinstance(rt, StepResult):
            return rt
        state = rt["state"]
        if skip_flag and state.get(skip_flag):
            return StepResult(True, summary=f"skipped ({skip_flag})")
        import importlib

        mod = importlib.import_module(f"agent.subgraphs.{phase_module}")
        wrapper = getattr(mod, wrapper_name)
        try:
            result = await wrapper(state)
        except Exception as exc:
            return StepResult(False, FailureKind.ESCALATE,
                              f"{wrapper_name} raised {type(exc).__name__}: {exc}")
        if isinstance(result, dict):
            state.update(result)
        if marker_after:
            rt["orch"]._persist_state(state["run_id"], marker_after)
        errors = result.get("errors") if isinstance(result, dict) else None
        summary = f"{wrapper_name} completed"
        if errors:
            return StepResult(False, FailureKind.ESCALATE,
                              f"{wrapper_name} reported errors: {errors[:2]}",
                              outputs={"errors": errors})
        return StepResult(True, summary=summary)

    return handler


async def _phase2_prepare(ctx: StepContext) -> StepResult:
    rt = _ensure_runtime(ctx)
    if isinstance(rt, StepResult):
        return rt
    orch, p2 = _import_parent()
    state = rt["state"]
    if state.get("skip_rebase_mode"):
        ctx.state["wave1_modules"] = []
        ctx.state["wave2_modules"] = []
        return StepResult(True, summary="skipped (skip_rebase_mode)")
    try:
        orch._run_pre_flight_curator(rt["settings"])
    except Exception:
        pass  # best-effort, mirrors the parent
    orch._persist_state(state["run_id"], "module_rebase")
    p2._save_phase2_progress(state["run_id"], state.get("modules", {}))
    return StepResult(True, summary="phase 2 prepared (curator + progress init)")


async def _module_rebase(ctx: StepContext) -> StepResult:
    rt = _ensure_runtime(ctx)
    if isinstance(rt, StepResult):
        return rt
    module = ctx.item
    if not module:
        return StepResult(True, summary="no module (empty wave)")
    _orch, p2 = _import_parent()
    from agent.nodes.phase2_rebase import node_rebase_module

    state = rt["state"]
    # honor the parent's own resume granularity: modules already done in the
    # resumed run are not re-rebased
    resume_prog = (state.get("_resume_extra") or {}).get("phase2_progress") or {}
    if resume_prog.get("run_id") == state.get("run_id"):
        prev = (resume_prog.get("modules") or {}).get(module) or {}
        if prev.get("status") in ("done", "skipped"):
            return StepResult(True, summary=f"module {module}: already "
                                            f"{prev['status']} (resumed)")
    result = await node_rebase_module({"module": module, **state})
    mod_result = (result or {}).get("modules", {}).get(module, {})
    state.setdefault("modules", {})[module] = {**state.get("modules", {}).get(module, {}),
                                               **mod_result}
    p2._save_phase2_progress(state["run_id"], state["modules"])

    status = mod_result.get("status")
    exit_code = mod_result.get("exit_code")
    attempts = mod_result.get("debug_attempts", 0)
    errors = (result or {}).get("errors") or []
    if status == "done":
        return StepResult(True, summary=f"module {module}: done")
    if any("ANTHROPIC_API_KEY" in str(e) for e in errors):
        return StepResult(False, FailureKind.BLOCKED,
                          f"module {module}: no ANTHROPIC_API_KEY")
    if exit_code == -1 and attempts == 0:
        return StepResult(False, FailureKind.RETRYABLE,
                          f"module {module}: agent errored before running "
                          f"({errors[:1]})")
    log = Path(ctx.state.get("parent_log_dir", "")) / "agents" / f"module-{module}.log"
    if bool(ctx.params.get("continue_on_module_failure")):
        return StepResult(True, summary=f"module {module}: FAILED (continuing — "
                                        "parity mode)",
                          outputs={"warning": f"{module} failed", "exit_code": exit_code})
    return StepResult(False, FailureKind.ESCALATE,
                      f"module {module} rebase failed after {attempts} debug "
                      f"attempt(s) — conflicts need a human",
                      outputs={"escalation_summary": {"module": module,
                                                      "exit_code": exit_code,
                                                      "debug_attempts": attempts},
                               "artifacts": [str(log)] if log.exists() else []})


async def _phase2_finalize(ctx: StepContext) -> StepResult:
    rt = _ensure_runtime(ctx)
    if isinstance(rt, StepResult):
        return rt
    state = rt["state"]
    rt["orch"]._persist_state(state["run_id"], "local_testing")
    ctx.state["touched_modules"] = [
        m for m, info in state.get("modules", {}).items()
        if (info or {}).get("status") in ("done", "failed")
    ]
    return StepResult(True, summary="phase 2 complete; marker -> local_testing",
                      outputs={"state_updates":
                               {"touched_modules": ctx.state["touched_modules"]}})


async def _phase4_guarded(ctx: StepContext) -> StepResult:
    """Copilot's push policy in front of the parent's Phase 4 (which pushes
    internally): refuse unless pushes are enabled."""
    rt = _ensure_runtime(ctx)
    if isinstance(rt, StepResult):
        return rt
    state = rt["state"]
    if state.get("local_ci_only_mode"):
        return StepResult(True, summary="skipped (local_ci_only_mode)")
    if not ctx.settings.allow_push:
        return StepResult(False, FailureKind.FORBIDDEN,
                          "phase 4 pushes to CI but ALLOW_PUSH=0 — run with "
                          "local_ci_only, or enable pushes deliberately")
    handler = _phase_step("phase4", "phase4_init_wrapper", None)
    return await handler(ctx)


async def _phase5(ctx: StepContext) -> StepResult:
    rt = _ensure_runtime(ctx)
    if isinstance(rt, StepResult):
        return rt
    handler = _phase_step("phase5", "phase5_init_wrapper", "done")
    result = await handler(ctx)
    if result.ok:
        try:
            rt["orch"]._run_post_run_curator(rt["settings"], rt["run_id"],
                                             Path(ctx.state.get("parent_log_dir", ".")))
        except Exception:
            pass  # post-run curator is best-effort in the parent too
        _RUNTIME.clear()  # run finished; next native run rebuilds fresh
    return result


async def _compare_with_locked(ctx: StepContext) -> StepResult:
    """Side-by-side validation artifact: native run vs a locked-run baseline."""
    import json

    baseline_file = ctx.params.get("baseline_status")
    lines = ["# Native vs locked comparison", ""]
    state = (ctx.state.get("rebase_state") or {})
    modules = state.get("modules", {})
    lines.append("## Native run")
    lines.append(f"- run: {ctx.state.get('rebase_run_id')}")
    for m, info in sorted(modules.items()):
        lines.append(f"- {m}: {(info or {}).get('status', '?')}")
    verdict = "unknown"
    if baseline_file and Path(baseline_file).exists():
        baseline = json.loads(Path(baseline_file).read_text())
        lines += ["", "## Locked baseline", f"- {baseline}"]
        native_failed = sum(1 for i in modules.values()
                            if (i or {}).get("status") == "failed")
        base_failed = (baseline.get("modules") or {}).get("failed", 0)
        verdict = ("worse" if native_failed > base_failed
                   else "better" if native_failed < base_failed else "equal")
    lines += ["", f"**verdict: {verdict}**"]
    path = ctx.run_dir / "COMPARISON.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    ctx.trace.record("native_comparison", verdict=verdict)
    return StepResult(True, summary=f"comparison written ({verdict})",
                      outputs={"verdict": verdict, "report": str(path)})


# self-registration (candidate playbook `repo-rebase-native`); this delegation
# layer wraps the parent package's own functions, so its handlers are a mix of
# factory-built and direct — registered imperatively rather than via @step.
register_step(StepSpec("rebase.prelude", "deterministic", "read", _prelude,
              "Parent runtime setup: settings/env/log dirs/stores + wave lists."))
register_step(StepSpec("rebase.phase1", "script", "write_workspace",
              _phase_step("phase1", "phase1_init_wrapper", "module_rebase",
                          skip_flag="skip_rebase_mode"),
              "Parent Phase 1 (init/merge/drift analysis) via its own wrapper."))
register_step(StepSpec("rebase.phase2_prepare", "deterministic", "read", _phase2_prepare,
              "Pre-flight curator + phase-2 progress init."))
register_step(StepSpec("rebase.module_rebase", "script", "write_workspace", _module_rebase,
              "One module rebase DELEGATED to the parent's node_rebase_module "
              "(the parent's own governed SDK loop + plan-review gate + debug "
              "retries) — kind=script because the agent runtime is the parent's."))
register_step(StepSpec("rebase.phase2_finalize", "deterministic", "read", _phase2_finalize,
              "Advance parent marker to local_testing after both waves."))
register_step(StepSpec("rebase.phase3", "validation", "write_workspace",
              _phase_step("phase3", "phase3_init_wrapper", "ci_e2e"),
              "Parent Phase 3 (local pipeline tests + SDK debug loops)."))
register_step(StepSpec("rebase.phase4", "script", "push", _phase4_guarded,
              "Parent Phase 4 (push + Buildkite CI), behind copilot's push guard."))
register_step(StepSpec("rebase.phase5", "report", "report", _phase5,
              "Parent Phase 5 (final summary) + post-run curator."))
register_step(StepSpec("rebase.compare_with_locked", "report", "report",
              _compare_with_locked,
              "COMPARISON.md: native run vs locked baseline (promotion evidence)."))
