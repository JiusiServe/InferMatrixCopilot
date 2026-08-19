"""Cursor harness transport — Strict on a Cursor subscription (M1).

Invocation shape proven by the Composer eval arm
(`eval/dataset/run_cursor_arm.py`): headless `cursor-agent --print --force
--output-format stream-json`, prompt on STDIN (argv has a 128KiB per-arg
limit on Linux and evidence packs exceed it), events parsed line-wise.

Governance (decision record in doc/features/provider-registry.md): cursor-agent
cannot fully disable its built-in tools, so the copilot's scoped tools are
OFFERED via the MCP tool bridge (preventive where used) and every session is
post-audited (`audit.py`) with the verdict traced — the detective fallback,
disclosed, never silent. The subprocess env is an allowlist: the vendor CLI
must keep its own subscription auth (HOME state) but must never inherit our
model-endpoint variables (this machine's ANTHROPIC_BASE_URL points at a
DeepSeek gateway) or repo credentials.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
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


class CursorTransport(HarnessTransport):
    """cursor-agent CLI as a Strict backend."""

    spec = PROVIDERS["cursor"]

    def auth_gap(self) -> str | None:
        cli = self.cli_path()
        if not cli:
            return None  # the CLI-missing gap is reported separately
        try:
            out = subprocess.run([cli, "status"], capture_output=True,
                                 text=True, encoding="utf-8", errors="replace",
                                 timeout=15, check=False)
        except (OSError, subprocess.SubprocessError):
            return None
        if "Logged in" not in f"{out.stdout}\n{out.stderr}":
            return "cursor-agent is not logged in — run: cursor-agent login"
        return None

    # -- process plumbing ----------------------------------------------------
    def _run(self, text: str, *, cwd: str, timeout_s: float,
             model: str = "") -> tuple[list[dict], bool]:
        """One CLI invocation → (parsed events, timed_out). A timeout kills
        the process but keeps the partial stream — a half-done investigation
        is salvage material, not garbage."""
        # --approve-mcps is load-bearing: headless runs do not auto-approve
        # configured MCP servers, and without it the tool bridge is silently
        # ignored (found in the live smoke — session ran on native tools only)
        cmd = [self.require_cli(), "--print", "--force", "--approve-mcps",
               "--output-format", "stream-json"]
        selected = model or self.settings.strict_backend_model
        if selected:
            cmd += ["--model", selected]
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
        for event in reversed(events):
            if event.get("type") == "result":
                return str(event.get("result") or "").strip()
        return ""

    @staticmethod
    def _usage(events: list[dict]) -> SessionUsage:
        """Best-effort: cursor-agent's usage/model reporting varies by
        version; absent fields stay 0/empty and cost stays None."""
        usage = SessionUsage()
        for event in events:
            model = event.get("model")
            if isinstance(model, str) and model:
                usage.served_model = model
            raw = event.get("usage")
            if isinstance(raw, dict):
                # live cursor-agent emits camelCase (inputTokens); accept
                # snake_case too so a future rename does not zero the counts
                usage.input_tokens += int(raw.get("inputTokens")
                                          or raw.get("input_tokens") or 0)
                usage.output_tokens += int(raw.get("outputTokens")
                                           or raw.get("output_tokens") or 0)
        return usage

    # -- MCP bridge wiring ---------------------------------------------------
    def _write_mcp_config(self, cwd: Path, spec_path: Path) -> list[Path]:
        """Project-scope `.cursor/mcp.json` in the session cwd pointing at the
        tool bridge. Returns the paths WE created (and only those) so the
        session can restore the tree afterwards — the cwd is our detached
        PR-time worktree and must not accumulate config litter."""
        import sys

        created: list[Path] = []
        cursor_dir = cwd / ".cursor"
        if not cursor_dir.exists():
            cursor_dir.mkdir()
            created.append(cursor_dir)
        config = cursor_dir / "mcp.json"
        if config.exists():  # never clobber a repo-committed config
            return created
        package_root = Path(__file__).resolve().parents[2]
        config.write_text(json.dumps({"mcpServers": {"infermatrix-tools": {
            "command": sys.executable,
            "args": ["-m", "infermatrix_copilot.tool_bridge",
                     "--spec", str(spec_path)],
            "env": {"PYTHONPATH": str(package_root)},
        }}}, indent=2), encoding="utf-8")
        created.insert(0, config)
        return created

    # -- transport contract --------------------------------------------------
    def run_session(self, req: AgentSessionRequest) -> AgentOutcome:
        from .audit import audit_events

        cwd = Path(req.scope.root or req.run_dir)
        created: list[Path] = []
        if req.bridge_spec_path is not None:
            created = self._write_mcp_config(cwd, req.bridge_spec_path)
        try:
            events, timed_out = self._run(
                f"{req.system}\n\n{req.prompt}", cwd=str(cwd),
                timeout_s=req.timeout_s, model=req.model)
        finally:
            for path in created:
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink(missing_ok=True)
        audit = audit_events(events, roots=(str(cwd), str(req.run_dir)),
                             read_only=req.scope.read_only, cwd=str(cwd))
        usage = self._usage(events)
        if req.trace is not None:
            req.trace.record(
                "harness_session", provider=self.spec.id, step=req.step_name,
                audit_ok=audit.ok, audit_violations=audit.violations[:10],
                shell_commands=audit.shell_commands,
                file_reads=audit.file_reads, writes=audit.writes,
                other_tool_calls=audit.other_tool_calls, timed_out=timed_out,
                served_model=usage.served_model)
        return AgentOutcome(
            text=self._final_text(events),
            iterations=0,  # the harness does not expose its round count
            tool_calls=audit.tool_calls,
            truncated=timed_out,
            refusals=[f"audit: {v}" for v in audit.violations],
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            tools_used=audit.tools_used[:40])

    def complete(self, *, system: str, messages: list[dict],
                 model: str = "", max_tokens: int | None = None,
                 role: str = "") -> Reply:
        """Tool-less one-shot. Runs in an EMPTY scratch cwd so cursor-agent's
        native tools have nothing to read — the containment for calls that
        need no repo at all (intent, reducer, repair)."""
        scratch = tempfile.mkdtemp(prefix="imc-cursor-oneshot-")
        try:
            events, timed_out = self._run(
                flatten_messages(system, messages), cwd=scratch,
                timeout_s=self.settings.strict_backend_timeout_s, model=model)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
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
