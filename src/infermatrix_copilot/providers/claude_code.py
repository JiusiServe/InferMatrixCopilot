"""Claude Code harness transport — Strict on a Claude subscription (M2).

The cleanest harness citizen (probed live 2026-08-14 on claude 2.1.232):
headless ``claude -p --output-format json`` returns ONE JSON object with
``result``, ``num_turns``, ``stop_reason``, ``total_cost_usd``, ``usage``
and per-model ``modelUsage``; ``--max-turns`` maps our iteration budget
natively; ``--system-prompt`` (+ ``--exclude-dynamic-system-prompt-
sections``) replaces the vendor system prompt with our step contract.

Tool governance is fully PREVENTIVE here, unlike cursor: built-in tools are
denied wholesale via ``--disallowedTools``, and only the MCP tool bridge is
allowed (``--mcp-config`` + ``--strict-mcp-config`` + ``--allowedTools
mcp__infermatrix-tools``), so every tool call flows through
``tools.dispatch`` — no native-tool audit needed. Session tool counts come
from the bridge trace delta.

Env is the shared allowlist (`base.sanitized_env`): the CLI must use its
own subscription auth from HOME, never an inherited ANTHROPIC_API_KEY /
ANTHROPIC_BASE_URL, and never see the host's CLAUDECODE marker.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ..agent_loop import AgentOutcome
from ..llm import Block, Reply
from .base import (
    AgentSessionRequest,
    HarnessTransport,
    SessionUsage,
    flatten_messages,
    sanitized_env,
)
from .registry import PROVIDERS

# Built-ins denied for every session: the bridge is the only tool surface.
_BUILTIN_DENY = ("Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch,"
                 "NotebookEdit,Task,TodoWrite")
_BRIDGE_SERVER = "infermatrix-tools"


class ClaudeCodeTransport(HarnessTransport):
    """claude CLI (headless) as a Strict backend."""

    spec = PROVIDERS["claude-code"]

    # -- process plumbing ----------------------------------------------------
    def _run(self, prompt_text: str, *, system: str, cwd: str,
             timeout_s: float, max_turns: int, model: str = "",
             mcp_config: Path | None = None) -> tuple[dict, bool]:
        """One CLI invocation → (parsed result object, timed_out). Prompt on
        stdin (argv has a 128KiB per-arg limit; evidence packs exceed it)."""
        cmd = [self.require_cli(), "-p", "--output-format", "json",
               "--max-turns", str(max_turns),
               "--disallowedTools", _BUILTIN_DENY]
        if system:
            cmd += ["--system-prompt", system,
                    "--exclude-dynamic-system-prompt-sections"]
        selected = model or self.settings.strict_backend_model
        if selected:
            cmd += ["--model", selected]
        if mcp_config is not None:
            cmd += ["--mcp-config", str(mcp_config), "--strict-mcp-config",
                    "--allowedTools", f"mcp__{_BRIDGE_SERVER}"]
        try:
            proc = subprocess.run(
                cmd, input=prompt_text, cwd=cwd, env=sanitized_env(),
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=timeout_s, check=False)
            stdout = proc.stdout or ""
        except subprocess.TimeoutExpired as exc:
            raw = exc.stdout or b""
            stdout = raw.decode("utf-8", "replace") if isinstance(raw, bytes) \
                else str(raw)
            return self._parse(stdout), True
        return self._parse(stdout), False

    @staticmethod
    def _parse(stdout: str) -> dict:
        """The single JSON object from -p json output; tolerant of stray
        warning lines before it."""
        start = stdout.find("{")
        if start < 0:
            return {}
        try:
            data = json.loads(stdout[start:])
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _usage(data: dict) -> SessionUsage:
        raw = data.get("usage") or {}
        usage = SessionUsage(
            input_tokens=int(raw.get("input_tokens") or 0),
            output_tokens=int(raw.get("output_tokens") or 0),
            cost_usd=(float(data["total_cost_usd"])
                      if data.get("total_cost_usd") is not None else None))
        # served model = the modelUsage entry that did the main work (max
        # cost); helper models (haiku sidecars) lose that comparison
        models = data.get("modelUsage") or {}
        if isinstance(models, dict) and models:
            usage.served_model = max(
                models, key=lambda m: float(
                    (models[m] or {}).get("costUSD") or 0))
        return usage

    def _write_mcp_config(self, spec_path: Path) -> Path:
        """The --mcp-config file, next to the bridge spec (never in the
        worktree — claude takes the config by flag, so nothing litters the
        session tree)."""
        package_root = Path(__file__).resolve().parents[2]
        config = spec_path.with_suffix(".mcp.json")
        config.write_text(json.dumps({"mcpServers": {_BRIDGE_SERVER: {
            "command": sys.executable,
            "args": ["-m", "infermatrix_copilot.tool_bridge",
                     "--spec", str(spec_path)],
            "env": {"PYTHONPATH": str(package_root)},
        }}}, indent=2), encoding="utf-8")
        return config

    @staticmethod
    def _bridge_activity(run_dir: Path, since_line: int) -> tuple[int, list[str]]:
        """(tool_calls, tools_used) from the bridge trace delta — with
        built-ins denied, bridged calls ARE the session's tool activity."""
        trace = run_dir / "bridge_trace.jsonl"
        if not trace.exists():
            return 0, []
        tools: list[str] = []
        for line in trace.read_text(encoding="utf-8").splitlines()[since_line:]:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("kind") == "tool_call":
                tools.append(str(event.get("tool") or "?"))
        return len(tools), tools

    @staticmethod
    def _trace_lines(run_dir: Path) -> int:
        trace = run_dir / "bridge_trace.jsonl"
        return len(trace.read_text(encoding="utf-8").splitlines()) \
            if trace.exists() else 0

    # -- transport contract --------------------------------------------------
    def run_session(self, req: AgentSessionRequest) -> AgentOutcome:
        cwd = str(req.scope.root or req.run_dir)
        mcp_config = (self._write_mcp_config(req.bridge_spec_path)
                      if req.bridge_spec_path is not None else None)
        before = self._trace_lines(req.run_dir)
        data, timed_out = self._run(
            req.prompt, system=req.system, cwd=cwd, timeout_s=req.timeout_s,
            max_turns=req.max_iters, model=req.model, mcp_config=mcp_config)
        usage = self._usage(data)
        tool_calls, tools_used = self._bridge_activity(req.run_dir, before)
        is_error = bool(data.get("is_error"))
        if req.trace is not None:
            req.trace.record(
                "harness_session", provider=self.spec.id, step=req.step_name,
                num_turns=data.get("num_turns"), is_error=is_error,
                timed_out=timed_out, cost_usd=usage.cost_usd,
                bridge_tool_calls=tool_calls,
                served_model=usage.served_model)
        return AgentOutcome(
            text=str(data.get("result") or ""),
            iterations=int(data.get("num_turns") or 0),
            tool_calls=tool_calls,
            truncated=timed_out or data.get("stop_reason") == "max_turns",
            refusals=[],
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            tools_used=tools_used[:40])

    def complete(self, *, system: str, messages: list[dict],
                 model: str = "", max_tokens: int | None = None,
                 role: str = "") -> Reply:
        """Tool-less one-shot: built-ins denied, no MCP config, two turns
        (one to think, the cap as a backstop). Runs in the run-less scratch
        of the process cwd — with every tool denied there is nothing to
        contain."""
        import tempfile

        with tempfile.TemporaryDirectory(prefix="imc-claude-oneshot-") as td:
            data, timed_out = self._run(
                flatten_messages("", messages), system=system, cwd=td,
                timeout_s=self.settings.strict_backend_timeout_s,
                max_turns=2, model=model)
        usage = self._usage(data)
        text = str(data.get("result") or "")
        return Reply(
            blocks=[Block(type="text", text=text)] if text else [],
            stop_reason="max_tokens" if timed_out else "end_turn",
            usage={"input_tokens": usage.input_tokens,
                   "output_tokens": usage.output_tokens,
                   "cache_read_input_tokens": int(
                       (data.get("usage") or {}).get(
                           "cache_read_input_tokens") or 0),
                   "cache_creation_input_tokens": int(
                       (data.get("usage") or {}).get(
                           "cache_creation_input_tokens") or 0)},
            model=usage.served_model)
