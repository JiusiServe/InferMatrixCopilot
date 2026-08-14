"""Post-run session audit for harness backends whose native tools cannot be
disabled (cursor-agent today).

Productized from the Composer eval arm (`eval/dataset/run_cursor_arm.py`),
which caught a live out-of-bounds read (`~/.claude/skills/...`) only through
exactly this check. Product policy audited here: file reads stay inside the
session's containment roots (the PR-time worktree + the run dir), and a
read-only scope means no write/edit tool calls. The eval arm layers its own
extra rule (no PR-discussion access) on top — that is a ground-truth-leakage
concern, not a product one, and deliberately does NOT live here.

Detective, not preventive — the disclosed fallback of the tool-governance
decision in doc/RFC-provider-registry.md. Findings are surfaced as
violations for the caller to trace and render in RUN_REPORT, never silently
dropped.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class SessionAudit:
    """The audited facts of one harness session: rule `violations` (empty =
    clean) and activity counters for the trace/report."""

    violations: list[str] = field(default_factory=list)
    shell_commands: int = 0
    file_reads: int = 0
    writes: int = 0
    other_tool_calls: int = 0
    tools_used: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    @property
    def tool_calls(self) -> int:
        return (self.shell_commands + self.file_reads + self.writes
                + self.other_tool_calls)


def contained_in(path: str, roots: tuple[str, ...]) -> bool:
    """True when `path` lies under any of `roots`. realpath both sides: this
    machine reaches the same worktree via /home and /data prefixes, and a
    symlinked HOME must not read as a violation. Shared with the tool
    bridge's preventive read containment."""
    real = os.path.realpath(path)
    return any(real == r or real.startswith(r + os.sep)
               for r in (os.path.realpath(r) for r in roots if r))


def audit_events(events: list[dict], *, roots: tuple[str, ...],
                 read_only: bool = True) -> SessionAudit:
    """Audit a cursor-agent stream-json event list. Each tool_call event
    appears twice (issue + result); only the issue (no "result" key) is
    counted so calls are not double-counted."""
    audit = SessionAudit()
    for event in events:
        if event.get("type") != "tool_call":
            continue
        tc = event.get("tool_call") or {}
        shell = tc.get("shellToolCall")
        if shell is not None:
            if "result" not in shell:
                audit.shell_commands += 1
                audit.tools_used.append("shell")
            continue
        read = tc.get("readToolCall")
        if read is not None:
            if "result" not in read:
                audit.file_reads += 1
                audit.tools_used.append("read")
                path = str((read.get("args") or {}).get("path") or "")
                if path and roots and not contained_in(path, roots):
                    audit.violations.append(
                        f"read outside session roots: {path[:160]}")
            continue
        write = tc.get("writeToolCall") or tc.get("editToolCall")
        if write is not None:
            if "result" not in write:
                audit.writes += 1
                audit.tools_used.append("write")
                if read_only:
                    audit.violations.append(
                        "write attempted in a read-only session")
            continue
        # anything else (MCP bridge tools included) — count, name best-effort
        for key, val in tc.items():
            if isinstance(val, dict) and "result" not in val:
                audit.other_tool_calls += 1
                audit.tools_used.append(key.removesuffix("ToolCall"))
                break
    return audit
