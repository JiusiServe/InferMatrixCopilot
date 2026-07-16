"""Only tool surface exposed to the evaluated model."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from .tool_policy import ToolDecision, ToolPolicy
from .trace_collector import TraceCollector


class ToolRefused(PermissionError):
    pass


class StaticToolExecutor:
    """Bounded read/search/git tools with complete trace and fail-closed checks."""

    def __init__(
        self,
        *,
        workspace: str | Path,
        allowed_commits: set[str],
        trace: TraceCollector,
        max_result_bytes: int = 256_000,
        max_git_calls: int = 40,
    ):
        self.workspace = Path(workspace).resolve()
        self.trace = trace
        self.max_result_bytes = max_result_bytes
        self.policy = ToolPolicy(
            workspace=self.workspace,
            allowed_commits=allowed_commits,
            max_git_calls=max_git_calls,
        )

    def _refuse(self, tool: str, reason: str, violation: str | None) -> None:
        self.trace.record("tool_call", tool=tool, status="refused", returned_bytes=0, reason=reason)
        if violation:
            self.trace.record("policy_violation", tool=tool, violation=violation, reason=reason)
        raise ToolRefused(reason)

    def _path(self, value: str | Path, *, tool: str) -> Path:
        result = self.policy.check_path(value)
        if result.decision == ToolDecision.REFUSE:
            self._refuse(tool, result.reason, result.violation)
        candidate = Path(value)
        return candidate.resolve() if candidate.is_absolute() else (self.workspace / candidate).resolve()

    def _bounded(self, value: str, *, tool: str) -> str:
        encoded = value.encode("utf-8", errors="replace")
        if len(encoded) > self.max_result_bytes:
            encoded = encoded[: self.max_result_bytes]
            value = encoded.decode("utf-8", errors="ignore") + "\n...[truncated]"
        self.trace.record("tool_call", tool=tool, status="succeeded", returned_bytes=len(value.encode("utf-8")))
        return value

    def read_file(self, path: str, *, start_line: int = 1, end_line: int | None = None) -> str:
        target = self._path(path, tool="read_file")
        if not target.is_file():
            self.trace.record("tool_call", tool="read_file", status="failed", returned_bytes=0, reason="not a file")
            raise FileNotFoundError(path)
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        if start_line < 1 or (end_line is not None and end_line < start_line):
            raise ValueError("invalid line range")
        selected = lines[start_line - 1 : end_line]
        return self._bounded("\n".join(selected), tool="read_file")

    def list_directory(self, path: str = ".", *, max_entries: int = 1000) -> list[str]:
        target = self._path(path, tool="list_directory")
        if not target.is_dir():
            self.trace.record("tool_call", tool="list_directory", status="failed", returned_bytes=0, reason="not a directory")
            raise NotADirectoryError(path)
        entries = sorted(child.relative_to(self.workspace).as_posix() for child in target.iterdir())[:max_entries]
        self.trace.record(
            "tool_call",
            tool="list_directory",
            status="succeeded",
            returned_bytes=sum(len(entry.encode("utf-8")) for entry in entries),
        )
        return entries

    def search_text(
        self,
        pattern: str,
        *,
        path: str = ".",
        regex: bool = False,
        max_results: int = 200,
    ) -> list[dict[str, Any]]:
        root = self._path(path, tool="search_text")
        matcher = re.compile(pattern) if regex else None
        results: list[dict[str, Any]] = []
        files = [root] if root.is_file() else (
            Path(current) / name
            for current, dirs, names in os.walk(root)
            for name in names
        )
        for file_path in files:
            if file_path.is_symlink() or ".git" in file_path.parts:
                continue
            try:
                text = file_path.read_text(encoding="utf-8", errors="replace")
            except (OSError, UnicodeError):
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                matched = bool(matcher.search(line)) if matcher else pattern in line
                if matched:
                    results.append({
                        "file": file_path.relative_to(self.workspace).as_posix(),
                        "line": line_number,
                        "text": line[:1000],
                    })
                    if len(results) >= max_results:
                        break
            if len(results) >= max_results:
                break
        payload_bytes = len(str(results).encode("utf-8"))
        self.trace.record("tool_call", tool="search_text", status="succeeded", returned_bytes=payload_bytes)
        return results

    def git(self, *args: str) -> str:
        command = "git " + " ".join(args)
        decision = self.policy.check_command(command)
        if decision.decision == ToolDecision.REFUSE:
            self._refuse("git_readonly", decision.reason, decision.violation)
        proc = subprocess.run(
            ["git", *args],
            cwd=self.workspace,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            reason = proc.stderr.decode("utf-8", errors="replace")[:4000]
            self.trace.record("tool_call", tool="git_readonly", status="failed", returned_bytes=0, reason=reason)
            raise RuntimeError(reason)
        return self._bounded(proc.stdout.decode("utf-8", errors="replace"), tool="git_readonly")
