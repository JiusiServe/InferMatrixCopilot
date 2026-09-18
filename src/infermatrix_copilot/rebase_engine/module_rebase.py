"""Per-module rebase execution — the neutral core of the parent's
`node_rebase_module` (prompt build → agent loop → substate result), with
every repo specific injected. Wave orchestration, foreach fan-out, and step
wiring land in the assembly PR; this module is the single-module unit they
compose.

Parent-parity behaviors: the module's result is SUBSTATE DATA (status/
turns), a loop failure marks the module failed (never raises through), and
the adaptive-guidance knowledge layer is best-effort via hooks."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from ..run_trace import RunTrace
from ..scopes import ToolScope
from .agent_loop import GATED_TOOL_NAMES, run_agent_loop
from .hooks import RebaseHooks
from .prompt_builder import (ModulePromptData, build_debug_prompt,
                             build_module_prompt)
from .substate import Substate


@dataclass(frozen=True)
class ModuleRunConfig:
    """Everything one module agent needs, assembled by the caller."""

    vllm_path: str
    omni_path: str
    script_dir: str
    model: str
    log_dir: str
    signal_dir: str = ""
    last_rebase_vllm_commit: str = ""
    cuda_devices: str = "0,1"
    hf_home: str = "/model"
    max_turns: int = 150
    # Harness backend selection (doc/features/provider-registry.md). "api"
    # keeps the in-process Anthropic tool-use loop; any other provider id
    # delegates the whole module step to that harness, with the SAME 20-tool
    # surface served through the MCP tool bridge.
    backend: str = "api"
    backend_model: str = ""       # model INSIDE the harness; see config
    settings: Any = None          # Settings — transport construction
    manifest_path: str = ""       # adapter manifest, rebuilt inside the bridge
    paths_spec: Mapping = field(default_factory=dict)  # serialized RebasePaths
    state_slice: Mapping = field(default_factory=dict)  # run state the backends read
    repo: str = ""                # repo name recorded in the bridge spec
    # Harness session bound. `max_iters` maps to a native turn cap only where
    # the harness HAS one (claude --max-turns); cursor/codex have none, so the
    # real bound there is this timeout plus the prompt's budget discipline.
    harness_timeout_s: float = 7200.0
    max_debug_retries: int = 3
    plan_review_max_rounds: int = 2
    model_aliases: Mapping[str, str] | None = None
    model_mismatch_policy: str = "fail"
    # adapter baseline ref (repo.remote/default_branch) — reaches the
    # LIVE prompt's test-plan prose (2026-08-01 neutrality audit)
    baseline_ref: str = "origin/main"


def _plan_gate_opened(run_dir: Path) -> bool:
    """Read `plan_done` back out of the bridge trace.

    The gate runs in the bridge process, so the parent cannot observe it
    directly; `PlanGate` records `plan_gate_opened` when a decision file is
    successfully written. Absent/unreadable trace ⇒ NOT opened (the same
    fail-closed default the in-process loop starts from)."""
    import json as _json
    tp = Path(run_dir) / "bridge_trace.jsonl"
    try:
        for line in tp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                if _json.loads(line).get("kind") == "plan_gate_opened":
                    return True
            except ValueError:
                continue
    except OSError:
        return False
    return False


async def _harness_attempt(prompt: str, *, module: str, config,
                           scope: ToolScope, trace: RunTrace,
                           tool_defs: list[dict], plan_prefix: str,
                           require_plan_review: bool) -> dict:
    """Delegate one module attempt to a harness backend.

    The harness runs its OWN loop, so the pieces `run_agent_loop` owns
    in-process move into the bridge: the 20-tool surface (rebuilt there from
    the spec) and the plan gate (enforced at dispatch, which a harness cannot
    bypass). Returns the same dict shape the in-process attempt does so
    `rebase_module`'s retry/debug logic is untouched.
    """
    import asyncio

    from ..providers import AgentSessionRequest
    from ..providers.registry import transport_for_id
    from ..tool_bridge import write_bridge_spec

    run_dir = Path(config.log_dir)
    transport = transport_for_id(config.settings, config.backend)
    spec_path = write_bridge_spec(
        run_dir=run_dir, step_name=f"rebase.module.{module}", scope=scope,
        repo=config.repo,
        rebase={
            "tool_schemas": str(Path(config.script_dir) / "tool_schemas.json"),
            "manifest_path": config.manifest_path,
            "model": config.model,
            # prebuilt upstream: serializing the checkout paths HERE would
            # add repo-specific vocabulary to a neutral core module
            "paths": dict(config.paths_spec or {}),
            "state": dict(config.state_slice or {}),
            "plan_write_prefix": plan_prefix if require_plan_review else "",
            "gated_tools": list(GATED_TOOL_NAMES),
        })
    # NEVER forward the tier model: it names a raw-API model the harness
    # does not have. Empty lets the transport fall back to its own setting.
    req = AgentSessionRequest(
        system=prompt, prompt="", scope=scope,
        model=config.backend_model or "",
        max_iters=config.max_turns, timeout_s=config.harness_timeout_s,
        run_dir=run_dir, step_name=f"rebase.module.{module}",
        bridge_spec_path=spec_path, trace=trace)
    outcome = await asyncio.to_thread(transport.run_session, req)
    return {"done": not getattr(outcome, "truncated", False),
            "text": getattr(outcome, "text", "") or "",
            "turns": int(getattr(outcome, "iterations", 0) or 0),
            "plan_done": (not require_plan_review
                          or _plan_gate_opened(run_dir))}


async def rebase_module(
    module: str,
    *,
    client: Any,
    config: ModuleRunConfig,
    prompt_data: ModulePromptData,
    tool_defs: list[dict],
    extra_tools: Mapping,
    substate: Substate,
    hooks: RebaseHooks | None = None,
    scope: ToolScope | None = None,
    trace: RunTrace | None = None,
    broken_imports: list[dict] | None = None,
    module_test_plan: dict | None = None,
) -> dict:
    """Run one module's rebase agent and record the outcome in substate.
    Returns the module's result dict (also written under
    ``modules.<module>``)."""
    hooks = hooks or RebaseHooks()
    try:
        guidance = hooks.adaptive_guidance(module)
    except Exception:  # noqa: BLE001 - knowledge layer never blocks a rebase
        guidance = ""

    prompt = build_module_prompt(
        module, prompt_data,
        vllm_path=config.vllm_path, omni_path=config.omni_path,
        script_dir=config.script_dir,
        last_rebase_vllm_commit=config.last_rebase_vllm_commit,
        cuda_devices=config.cuda_devices, hf_home=config.hf_home,
        log_dir=config.log_dir, signal_dir=config.signal_dir,
        rebase_run_id=substate.run_id,
        max_debug_retries=config.max_debug_retries,
        plan_review_max_rounds=config.plan_review_max_rounds,
        broken_imports=broken_imports, module_test_plan=module_test_plan,
        adaptive_guidance=guidance, live=True,
        baseline_ref=config.baseline_ref)

    substate.update({"modules": {module: {"status": "running"}}})
    agent_log = str(Path(config.log_dir) / "agents" / f"module-{module}.log")
    Path(agent_log).parent.mkdir(parents=True, exist_ok=True)
    plan_prefix = str(Path(config.log_dir) / "plans" / f"module-{module}")

    async def _attempt(p: str, *, require_plan_review: bool = True) -> dict:
        try:
            if config.backend and config.backend != "api":
                return await _harness_attempt(
                    p, module=module, config=config, scope=scope, trace=trace,
                    tool_defs=tool_defs, plan_prefix=plan_prefix,
                    require_plan_review=require_plan_review)
            return await run_agent_loop(
                client, p, model=config.model, tool_defs=tool_defs,
                extra_tools=extra_tools, scope=scope, trace=trace,
                max_turns=config.max_turns, plan_write_prefix=plan_prefix,
                require_plan_review=require_plan_review,
                model_aliases=config.model_aliases,
                model_mismatch_policy=config.model_mismatch_policy,
                agent_log=agent_log)
        except Exception as exc:  # noqa: BLE001 - failure is substate data
            return {"done": False, "text": f"agent loop error: {exc}",
                    "turns": 0, "plan_done": False}

    # parent parity: an incomplete first run gets up to max_debug_retries
    # follow-up attempts with the debug prompt built from the failure text.
    # The plan gate PERSISTS across attempts: once the module's decision was
    # written, debug retries run unlocked (the debug prompt carries no
    # plan-review contract, and the parent's re-locking left debug agents
    # unable to edit — a fixed, recorded parent defect); an initial run that
    # never passed the gate keeps it closed for retries.
    debug_attempts = 0
    result = await _attempt(prompt)
    gate_passed = bool(result.get("plan_done"))
    while not result.get("done") and \
            debug_attempts < config.max_debug_retries:
        debug_attempts += 1
        debug_prompt = build_debug_prompt(
            module, result.get("text", ""),
            prompt_data.debug_prompt_template, "")
        result = await _attempt(debug_prompt,
                                require_plan_review=not gate_passed)
        gate_passed = gate_passed or bool(result.get("plan_done"))

    outcome = {"status": "done" if result.get("done") else "failed",
               "exit_code": 0 if result.get("done") else -1,
               "debug_attempts": debug_attempts,
               "turns": result.get("turns", 0),
               "summary": (result.get("text") or "")[:2000]}
    substate.update({"modules": {module: outcome}})
    try:
        hooks.on_module_result(module, outcome)
    except Exception:  # noqa: BLE001 - observation hook never raises through
        pass
    return outcome
