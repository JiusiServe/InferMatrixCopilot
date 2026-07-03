"""Tool layer: atomic capabilities dispatched through one scope-enforcing choke point.

Tools are NOT steps (design §3.X.2): they only express "what can be done".
Every call is scope-checked and traced; out-of-scope writes execute but are
recorded — never silent.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .run_trace import RunTrace
from .scopes import ToolScope


@dataclass(frozen=True)
class ToolDef:
    name: str
    description: str
    input_schema: dict
    handler: Callable[..., str]
    write_path_arg: str | None = None  # arg holding the path a write lands on


def _read_file(path: str, max_bytes: int = 200_000, **_: Any) -> str:
    data = Path(path).read_text(encoding="utf-8", errors="replace")
    return data[:max_bytes]


def _write_file(path: str, content: str, **_: Any) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"wrote {len(content)} chars to {path}"


def _edit_file(path: str, old: str, new: str, **_: Any) -> str:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    n = text.count(old)
    if n == 0:
        raise ValueError("old text not found — edit rejected, re-read the file")
    if n > 1:
        raise ValueError(f"old text matches {n} times — must match exactly once")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    return f"edited {path}"


def _list_dir(path: str, **_: Any) -> str:
    return "\n".join(sorted(x.name + ("/" if x.is_dir() else "") for x in Path(path).iterdir()))


def _grep(pattern: str, path: str, **_: Any) -> str:
    out = subprocess.run(
        ["grep", "-rn", "--include=*", "-e", pattern, path],
        capture_output=True, text=True, timeout=60,
    )
    return out.stdout[:20_000] or "(no matches)"


def _run_shell(cmd: str, cwd: str | None = None, timeout: int = 600, **_: Any) -> str:
    out = subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )
    return f"exit={out.returncode}\n{out.stdout[-10_000:]}\n{out.stderr[-5_000:]}"


def _schema(props: dict, required: list[str]) -> dict:
    return {"type": "object", "properties": props, "required": required}


_S = {"type": "string"}
TOOLS: dict[str, ToolDef] = {
    t.name: t
    for t in [
        ToolDef("read_file", "Read a text file.", _schema({"path": _S}, ["path"]), _read_file),
        ToolDef("write_file", "Write/overwrite a file.",
                _schema({"path": _S, "content": _S}, ["path", "content"]), _write_file, "path"),
        ToolDef("edit_file", "Replace exactly-once-matching text in a file.",
                _schema({"path": _S, "old": _S, "new": _S}, ["path", "old", "new"]), _edit_file, "path"),
        ToolDef("list_dir", "List a directory.", _schema({"path": _S}, ["path"]), _list_dir),
        ToolDef("grep", "Recursive text search.",
                _schema({"pattern": _S, "path": _S}, ["pattern", "path"]), _grep),
        ToolDef("run_shell", "Run a shell command.",
                _schema({"cmd": _S, "cwd": _S}, ["cmd"]), _run_shell),
    ]
}


def tool_definitions_for(scope: ToolScope | None,
                         extra: dict[str, ToolDef] | None = None) -> list[dict]:
    """Anthropic-format tool defs: builtin tools filtered to the scope's
    allowed set, plus step-provided extra tools (already vetted by the step)."""
    names = scope.allowed_tools if scope else set(TOOLS)
    defs = [
        {"name": t.name, "description": t.description, "input_schema": t.input_schema}
        for t in TOOLS.values()
        if t.name in names
    ]
    for t in (extra or {}).values():
        defs.append({"name": t.name, "description": t.description,
                     "input_schema": t.input_schema})
    return defs


def dispatch(
    name: str,
    args: dict,
    *,
    scope: ToolScope | None = None,
    trace: RunTrace | None = None,
    extra: dict[str, ToolDef] | None = None,
) -> dict:
    """Returns {"ok": bool, "result"|"error": str, "out_of_scope": bool}."""
    tool = (extra or {}).get(name) or TOOLS.get(name)
    if tool is None:
        return {"ok": False, "error": f"unknown tool: {name}", "out_of_scope": False}
    if extra and name in extra:  # extra tools bypass the builtin allowlist only
        try:
            result = tool.handler(**args)
            if trace:
                trace.record("tool_call", tool=name, ok=True, out_of_scope=False,
                             path=None)
            return {"ok": True, "result": result, "out_of_scope": False}
        except Exception as exc:
            if trace:
                trace.record("tool_call", tool=name, ok=False, out_of_scope=False,
                             path=None)
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}",
                    "out_of_scope": False}

    write_path = args.get(tool.write_path_arg) if tool.write_path_arg else None
    out_of_scope = False
    if scope is not None:
        decision = scope.check(name, write_path=write_path)
        if not decision.allowed:
            if trace:
                trace.record("tool_refused", tool=name, reason=decision.reason)
            return {"ok": False, "error": f"refused: {decision.reason}", "out_of_scope": False}
        out_of_scope = decision.out_of_scope

    try:
        result = tool.handler(**args)
        ok = True
        payload: dict = {"ok": True, "result": result, "out_of_scope": out_of_scope}
    except Exception as exc:  # errors are observations, not crashes
        ok = False
        payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}", "out_of_scope": out_of_scope}

    if trace:
        trace.record(
            "tool_call", tool=name, ok=ok, out_of_scope=out_of_scope,
            path=str(write_path) if write_path else None,
        )
        if out_of_scope:
            trace.record("out_of_scope_edit", tool=name, path=str(write_path))
        if name == "write_file" and write_path and Path(write_path).suffix == ".py":
            trace.record("full_file_write", path=str(write_path))
    return payload
