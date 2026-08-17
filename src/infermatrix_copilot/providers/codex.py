"""Codex CLI harness transport — Strict on a ChatGPT subscription (M3).

``codex exec --json`` emits JSONL events; the final agent message is the
session's answer and ``turn.completed`` events carry token usage. Probed on
codex-cli 0.145.0 (auth was absent on the dev machine, so unlike cursor/
claude-code this transport is exercised offline against recorded shapes —
the readiness path reports the login gap before any run starts).

Governance posture (disclosed, per doc/features/provider-registry.md): codex
cannot disable its native shell, but ``--sandbox read-only`` is an OS-level
PREVENTIVE guarantee against writes and network egress; the MCP tool
bridge is offered alongside via ``-c mcp_servers...`` overrides so scoped
reads flow through ``tools.dispatch``. Broad *reads* inside the sandbox
remain possible and are a documented limitation of this backend class.

Env is the shared allowlist (`base.sanitized_env`); codex keeps its own
auth under HOME (~/.codex)."""

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

_BRIDGE_SERVER = "infermatrix-tools"


class CodexTransport(HarnessTransport):
    """codex CLI (exec mode) as a Strict backend."""

    spec = PROVIDERS["codex"]

    def auth_gap(self) -> str | None:
        cli = self.cli_path()
        if not cli:
            return None  # the CLI-missing gap is reported separately
        try:
            out = subprocess.run([cli, "login", "status"], capture_output=True,
                                 text=True, encoding="utf-8", errors="replace",
                                 timeout=15, check=False)
        except (OSError, subprocess.SubprocessError):
            return None  # status probe itself broken — let the run surface it
        blob = f"{out.stdout}\n{out.stderr}"
        if out.returncode != 0 or "Not logged in" in blob:
            return ("codex CLI is not logged in — run: codex login "
                    "(ChatGPT subscription auth)")
        return None

    # -- process plumbing ----------------------------------------------------
    def _mcp_overrides(self, spec_path: Path) -> list[str]:
        """``-c`` config overrides wiring the tool bridge as an MCP server —
        config-only, so nothing is written into the session tree."""
        package_root = Path(__file__).resolve().parents[2]
        args = json.dumps(["-m", "infermatrix_copilot.tool_bridge",
                           "--spec", str(spec_path)])
        return [
            "-c", f'mcp_servers.{_BRIDGE_SERVER}.command="{sys.executable}"',
            "-c", f"mcp_servers.{_BRIDGE_SERVER}.args={args}",
            "-c", (f"mcp_servers.{_BRIDGE_SERVER}.env="
                   f'{{PYTHONPATH = "{package_root}"}}'),
        ]

    def _run(self, text: str, *, cwd: str, timeout_s: float, model: str = "",
             mcp_spec: Path | None = None) -> tuple[list[dict], bool]:
        """One CLI invocation → (parsed events, timed_out). Prompt on stdin
        (the ``-`` positional; argv has a 128KiB per-arg limit)."""
        cmd = [self.require_cli(), "exec", "--json", "-s", "read-only",
               "--skip-git-repo-check", "-C", cwd]
        selected = model or self.settings.strict_backend_model
        if selected:
            cmd += ["-m", selected]
        if mcp_spec is not None:
            cmd += self._mcp_overrides(mcp_spec)
        cmd += ["-"]
        timed_out = False
        try:
            proc = subprocess.run(
                cmd, input=text, cwd=cwd, env=sanitized_env(),
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=timeout_s, check=False)
            stdout = proc.stdout or ""
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            raw = exc.stdout or b""
            stdout = raw.decode("utf-8", "replace") if isinstance(raw, bytes) \
                else str(raw)
        events: list[dict] = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events, timed_out

    @staticmethod
    def _final_text(events: list[dict]) -> str:
        """The last agent message. Shape is version-dependent — accept both
        the item.completed/agent_message form and any event carrying an
        agent message text field."""
        last = ""
        for event in events:
            item = event.get("item")
            if isinstance(item, dict):
                kind = item.get("item_type") or item.get("type") or ""
                if "agent_message" in str(kind) and item.get("text"):
                    last = str(item["text"])
        return last.strip()

    @staticmethod
    def _usage(events: list[dict]) -> SessionUsage:
        usage = SessionUsage()
        for event in events:
            raw = event.get("usage")
            if isinstance(raw, dict):
                usage.input_tokens += int(raw.get("input_tokens") or 0)
                usage.output_tokens += int(raw.get("output_tokens") or 0)
            model = event.get("model")
            if isinstance(model, str) and model:
                usage.served_model = model
        return usage

    @staticmethod
    def _tool_activity(events: list[dict]) -> list[str]:
        """Names of non-message items the session completed (commands, MCP
        tool calls…) — codex's specific item types vary by version, so this
        is a best-effort activity log, not an audit (the sandbox is the
        enforcement layer)."""
        used: list[str] = []
        for event in events:
            item = event.get("item")
            if isinstance(item, dict):
                kind = str(item.get("item_type") or item.get("type") or "")
                if kind and "agent_message" not in kind \
                        and "reasoning" not in kind:
                    used.append(kind)
        return used

    # -- transport contract --------------------------------------------------
    def run_session(self, req: AgentSessionRequest) -> AgentOutcome:
        cwd = str(req.scope.root or req.run_dir)
        events, timed_out = self._run(
            f"{req.system}\n\n{req.prompt}", cwd=cwd,
            timeout_s=req.timeout_s, model=req.model,
            mcp_spec=req.bridge_spec_path)
        usage = self._usage(events)
        used = self._tool_activity(events)
        if req.trace is not None:
            req.trace.record(
                "harness_session", provider=self.spec.id, step=req.step_name,
                timed_out=timed_out, item_count=len(events),
                tool_items=len(used), served_model=usage.served_model)
        return AgentOutcome(
            text=self._final_text(events),
            iterations=0,  # codex does not expose a turn budget/counter
            tool_calls=len(used),
            truncated=timed_out,
            refusals=[],
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            tools_used=used[:40])

    def complete(self, *, system: str, messages: list[dict],
                 model: str = "", max_tokens: int | None = None,
                 role: str = "") -> Reply:
        """Tool-less one-shot in an empty scratch cwd (read-only sandbox +
        nothing to read = contained)."""
        import tempfile

        with tempfile.TemporaryDirectory(prefix="imc-codex-oneshot-") as td:
            events, timed_out = self._run(
                flatten_messages(system, messages), cwd=td,
                timeout_s=self.settings.strict_backend_timeout_s, model=model)
        usage = self._usage(events)
        text = self._final_text(events)
        return Reply(
            blocks=[Block(type="text", text=text)] if text else [],
            stop_reason="max_tokens" if timed_out else "end_turn",
            usage={"input_tokens": usage.input_tokens,
                   "output_tokens": usage.output_tokens,
                   "cache_read_input_tokens": 0,
                   "cache_creation_input_tokens": 0},
            model=usage.served_model)
