"""Rebuild the existing rebase tool pack in the harness's MCP process.

The parent supplies resolved paths and its scrubbed target environment, so
tests use the same runtime as API agents. Only this dispatcher can write;
the Codex native sandbox stays read-only throughout the session.
"""

from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from ...adapters.base import expand_path
from ...config import Settings
from ...run_trace import RunTrace
from ...scopes import ToolScope
from ...tools import dispatch
from ...rebase_engine.rebase_tools import RebasePaths, build_rebase_tools


def rebase_bridge_config(ctx, manifest: dict, paths: RebasePaths,
                         tool_defs: list[dict], *, module: str,
                         require_plan_review: bool) -> dict:
    """Serialize only the configuration consumed by the rebase backends.

    No API credentials are needed: the plan reviewer uses the selected
    subscription harness. Runtime paths are resolved before environment
    sanitization removes the adapter's shell variables.
    """
    settings_keys = {
        "adapters_dir", "knowledge_dir", "skills_dir", "memory_db",
        "imx_knowledge_runtime", "strict_backend", "strict_backend_model",
        "strict_backend_cli", "strict_backend_timeout_s", "rebase_reviewer_model",
    }
    resolved_manifest = deepcopy(manifest)
    knowledge = (resolved_manifest.get("rebase") or {}).get("knowledge") or {}
    for key in ("parent_debug_db", "parent_skills_dir"):
        if knowledge.get(key):
            knowledge[key] = expand_path(
                str(knowledge[key]), extra=ctx.settings.expansion_env())
    task = ctx.state.get("task_spec") or {}
    return {
        "settings": ctx.settings.model_dump(mode="json", include=settings_keys),
        "manifest": resolved_manifest,
        "paths": asdict(paths),
        "tool_defs": tool_defs,
        "state": {
            "run_id": ctx.state.get("run_id") or ctx.run_dir.name,
            "upstream_commit": ctx.state.get("upstream_commit", ""),
            "task_spec": {"repo": task.get("repo", ""),
                          "mode": task.get("mode", "eco")},
        },
        "plan_dir": str(ctx.run_dir / "plans" / f"module-{module}"),
        "require_plan_review": require_plan_review,
    }


def rebase_dispatcher(scope: ToolScope, spec: dict, trace: RunTrace):
    """Return the real tool pack and its plan-gated dispatch function."""
    # Imported lazily because engine steps import this bridge when dispatching
    # a module; the standalone MCP process reconstructs only the backend pack.
    from ..steps.rebase_v3 import _build_backends

    data = spec["rebase"]
    settings = Settings(_env_file=None, **data["settings"])
    ctx = SimpleNamespace(settings=settings, state=data["state"],
                          run_dir=Path(spec["run_dir"]), trace=trace)
    paths = RebasePaths(**data["paths"])
    target = settings.tier_target(data["state"]["task_spec"].get("mode", "eco"))
    tools = build_rebase_tools(
        data["tool_defs"], paths,
        _build_backends(ctx, data["manifest"], paths.omni_path, target,
                        agent_env=dict(paths.env)))
    plan_dir = Path(data["plan_dir"]).resolve()
    plan_done = not data["require_plan_review"] or any(
        plan_dir.rglob("*.decision.md"))
    reviewed_plans: set[Path] = set()
    read_roots = tuple(Path(p).resolve() for p in
                       (paths.omni_path, paths.vllm_path, spec["run_dir"]) if p)
    execution_tools = {"edit_file", "run_shell", "run_pytest", "reproduce",
                       "run_import_check", "run_precommit"}

    def call(name: str, arguments: dict) -> str:
        nonlocal plan_done

        def refuse(reason: str) -> None:
            trace.record("tool_refused", tool=name, reason=reason)
            raise RuntimeError(reason)

        args = dict(arguments)
        path_keys = {
            "read_file": "file_path", "write_file": "file_path",
            "edit_file": "file_path", "grep": "path", "run_shell": "workdir",
        }
        key = path_keys.get(name)
        path = None
        if key and args.get(key):
            path = Path(args[key])
            path = (path if path.is_absolute() else Path(paths.omni_path) / path).resolve()
            args[key] = str(path)
            if not any(path.is_relative_to(root) for root in read_roots):
                refuse("path outside rebase checkout/upstream/run directory")
        if name == "request_plan_review":
            for key in ("plan_json_path", "plan_md_path"):
                candidate = Path(args.get(key) or "").resolve()
                if not candidate.is_relative_to(plan_dir):
                    refuse("plan review files must be inside the module plan directory")
        if not plan_done:
            if name in execution_tools:
                refuse(f"{name} is locked until the plan-review decision is written")
            if name == "write_file":
                if path is None or not path.is_relative_to(plan_dir):
                    refuse("write_file is locked outside the module plan directory")
                if path.name.endswith(".decision.md"):
                    plan_json = path.with_name(path.name.removesuffix(".decision.md") + ".json")
                    if plan_json not in reviewed_plans:
                        refuse("call request_plan_review for this plan before writing its decision")
        result = dispatch(name, args, scope=scope, trace=trace, extra=tools)
        if not result["ok"]:
            raise RuntimeError(str(result.get("error") or "rebase tool failed"))
        payload = json.loads(result["result"])
        if name == "request_plan_review":
            # The established contract permits an explicit decision after a
            # failed review attempt. The failure remains visible in the trace
            # and tool result; it never masquerades as reviewer approval.
            reviewed_plans.add(Path(args["plan_json_path"]).resolve())
        if name == "write_file" and path is not None and \
                path.name.endswith(".decision.md") and "error" not in payload:
            plan_done = True
        return result["result"]

    return tools, call


def register_rebase_tools(mcp, scope: ToolScope, spec: dict,
                          trace: RunTrace) -> None:
    """Advertise the adapter's exact schemas using FastMCP's MCP server.

    The low-level handlers preserve existing schemas instead of turning the
    handlers' ``**kwargs`` into a different, unusable generated schema.
    """
    from mcp.types import TextContent, Tool

    tools, call = rebase_dispatcher(scope, spec, trace)

    @mcp._mcp_server.list_tools()
    async def list_tools():
        return [Tool(name=t.name, description=t.description,
                     inputSchema=t.input_schema) for t in tools.values()]

    @mcp._mcp_server.call_tool()
    async def call_tool(name: str, arguments: dict):
        result = await asyncio.to_thread(call, name, arguments)
        return [TextContent(type="text", text=result)]
