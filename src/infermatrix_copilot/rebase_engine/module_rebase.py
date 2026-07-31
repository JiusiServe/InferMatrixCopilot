"""Per-module rebase execution — the neutral core of the parent's
`node_rebase_module` (prompt build → agent loop → substate result), with
every repo specific injected. Wave orchestration, foreach fan-out, and step
wiring land in the assembly PR; this module is the single-module unit they
compose.

Parent-parity behaviors: the module's result is SUBSTATE DATA (status/
turns), a loop failure marks the module failed (never raises through), and
the adaptive-guidance knowledge layer is best-effort via hooks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ..run_trace import RunTrace
from ..scopes import ToolScope
from .agent_loop import run_agent_loop
from .hooks import RebaseHooks
from .prompt_builder import ModulePromptData, build_module_prompt
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
    plan_review_max_rounds: int = 2
    model_aliases: Mapping[str, str] | None = None
    model_mismatch_policy: str = "fail"


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
        plan_review_max_rounds=config.plan_review_max_rounds,
        broken_imports=broken_imports, module_test_plan=module_test_plan,
        adaptive_guidance=guidance)

    substate.update({"modules": {module: {"status": "running"}}})
    agent_log = str(Path(config.log_dir) / "agents" / f"module-{module}.log")
    Path(agent_log).parent.mkdir(parents=True, exist_ok=True)
    plan_prefix = str(Path(config.log_dir) / "plans" / f"module-{module}")

    try:
        result = await run_agent_loop(
            client, prompt, model=config.model, tool_defs=tool_defs,
            extra_tools=extra_tools, scope=scope, trace=trace,
            max_turns=config.max_turns, plan_write_prefix=plan_prefix,
            model_aliases=config.model_aliases,
            model_mismatch_policy=config.model_mismatch_policy,
            agent_log=agent_log)
    except Exception as exc:  # noqa: BLE001 - module failure is substate data
        result = {"done": False, "text": f"agent loop error: {exc}",
                  "turns": 0}

    outcome = {"status": "done" if result.get("done") else "failed",
               "turns": result.get("turns", 0),
               "summary": (result.get("text") or "")[:2000]}
    substate.update({"modules": {module: outcome}})
    try:
        hooks.on_module_result(module, outcome)
    except Exception:  # noqa: BLE001 - observation hook never raises through
        pass
    return outcome
