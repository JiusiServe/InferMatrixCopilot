"""Scoped-tool MCP bridge for harness backends (doc/RFC-provider-registry.md).

Entry: ``python -m infermatrix_copilot.tool_bridge --spec <bridge_spec.json>``
— an stdio MCP server a harness session launches from its MCP config. It
exposes the run's builtin tools plus knowledge doc search/read, and every
builtin call passes ``tools.dispatch`` with the step's deserialized
`ToolScope`, so refusals, relative-path resolution against the PR-time
worktree, and result bounds behave identically to the in-process loop.

Two things are deliberately STRONGER than the in-process loop:

- **Read containment.** `ToolScope` path-guards only writes; a harness is a
  less-trusted caller holding an untrusted PR diff, so the bridge refuses
  read/list/grep targets outside the containment roots (scope root + run
  dir) — the `.env`-exfiltration guard.
- **Separate trace file.** Tool events append to ``bridge_trace.jsonl``
  next to the spec; a second process must not interleave with the parent's
  ``run_trace.jsonl``.

Known M1 gap, disclosed: the in-process extra tools built from a live
`StepContext` (skill/memory retrieval, repo_map) are not reconstructed here
— harness sessions get builtins + doc_search/doc_read.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from .run_trace import RunTrace
from .scopes import PathScope, ToolScope
from .tools import _PATH_ARGS, TOOLS, dispatch

_SPEC_VERSION = 1


# -- spec serialization ------------------------------------------------------
def write_bridge_spec(*, run_dir: Path, step_name: str, scope: ToolScope,
                      repo: str) -> Path:
    """Serialize one step's tool surface under ``<run_dir>/bridge/``. The
    filename is sanitized from the step name (ensemble steps carry ``#``)."""
    bridge_dir = Path(run_dir) / "bridge"
    bridge_dir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", step_name or "step") or "step"
    path = bridge_dir / f"{stem}.json"
    ps = scope.path_scope
    path.write_text(json.dumps({
        "version": _SPEC_VERSION,
        "scope": {
            "name": scope.name,
            "allowed_tools": sorted(scope.allowed_tools),
            "read_only": scope.read_only,
            "root": scope.root,
            "path_scope": {"writable": list(ps.writable),
                           "primary": list(ps.primary)} if ps else None,
        },
        "repo": repo,
        "run_dir": str(run_dir),
        "trace_path": str(Path(run_dir) / "bridge_trace.jsonl"),
    }, indent=2), encoding="utf-8")
    return path


def load_bridge_spec(path: Path) -> tuple[ToolScope, dict]:
    """Deserialize a spec back into a `ToolScope` + the raw dict."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("version") != _SPEC_VERSION:
        raise ValueError(f"unsupported bridge spec version: {data.get('version')!r}")
    s = data["scope"]
    ps = s.get("path_scope")
    scope = ToolScope(
        name=str(s["name"]),
        allowed_tools=frozenset(s["allowed_tools"]),
        path_scope=PathScope(writable=tuple(ps["writable"]),
                             primary=tuple(ps["primary"])) if ps else None,
        read_only=bool(s["read_only"]),
        root=str(s.get("root") or ""),
    )
    return scope, data


# -- server ------------------------------------------------------------------
def make_dispatcher(scope: ToolScope, roots: tuple[str, ...], trace: RunTrace):
    """The bridge's call path: read containment (stronger than ToolScope,
    which path-guards only writes — see module docstring) and then the same
    `tools.dispatch` the in-process loop uses. Errors raise so the MCP layer
    marks the tool result as an error. Module-level so the guard is testable
    without the MCP SDK installed."""
    from .providers.audit import contained_in

    def _call(name: str, args: dict) -> str:
        key = _PATH_ARGS.get(name)
        if key is not None and roots:
            # mirror dispatch's relative-path resolution BEFORE containment,
            # so the checked path is the one that would actually be touched
            target = args.get(key)
            if isinstance(target, str) and target and not os.path.isabs(target):
                target = os.path.join(roots[0], target)
            if isinstance(target, str) and target and not contained_in(target, roots):
                trace.record("tool_refused", tool=name,
                             reason=f"path outside session roots: {target}")
                raise RuntimeError(
                    f"refused: {name} target is outside this session's "
                    "worktree/run dir")
        out = dispatch(name, args, scope=scope, trace=trace)
        if not out["ok"]:
            raise RuntimeError(str(out.get("error") or "tool error"))
        return str(out["result"])

    return _call


def build_server(spec_path: Path):
    """Build the FastMCP server for one spec. Import of the MCP SDK is local
    so the module stays importable (spec read/write) without the extra."""
    from mcp.server.fastmcp import FastMCP

    scope, spec = load_bridge_spec(spec_path)
    trace = RunTrace(Path(spec["trace_path"]))
    roots = tuple(r for r in (scope.root, spec.get("run_dir", "")) if r)
    _call = make_dispatcher(scope, roots, trace)

    mcp = FastMCP("infermatrix-tool-bridge")
    allowed = scope.allowed_tools & set(TOOLS)

    if "read_file" in allowed:
        @mcp.tool(description=TOOLS["read_file"].description)
        def read_file(path: str, offset: int = 0) -> str:
            return _call("read_file", {"path": path, "offset": offset})

    if "list_dir" in allowed:
        @mcp.tool(description=TOOLS["list_dir"].description)
        def list_dir(path: str) -> str:
            return _call("list_dir", {"path": path})

    if "grep" in allowed:
        @mcp.tool(description=TOOLS["grep"].description)
        def grep(pattern: str, path: str, regex: bool = False) -> str:
            return _call("grep", {"pattern": pattern, "path": path,
                                  "regex": regex})

    if "write_file" in allowed:
        @mcp.tool(description=TOOLS["write_file"].description)
        def write_file(path: str, content: str) -> str:
            return _call("write_file", {"path": path, "content": content})

    if "edit_file" in allowed:
        @mcp.tool(description=TOOLS["edit_file"].description)
        def edit_file(path: str, old: str, new: str) -> str:
            return _call("edit_file", {"path": path, "old": old, "new": new})

    if "run_shell" in allowed:
        @mcp.tool(description=TOOLS["run_shell"].description)
        def run_shell(cmd: str, cwd: str = "") -> str:
            return _call("run_shell", {"cmd": cmd, "cwd": cwd or None})

    _register_knowledge_tools(mcp, spec, scope, trace)
    return mcp


def _bridge_ctx(spec: dict, scope: ToolScope, trace: RunTrace):
    """A minimal StepContext view for the agent-runtime knowledge factories:
    they consume only settings / state / run_dir / trace, all of which the
    bridge spec can reconstruct."""
    from types import SimpleNamespace

    from .config import Settings

    return SimpleNamespace(
        settings=Settings(),
        state={"task_spec": {"repo": spec.get("repo", "")},
               "repo_path": scope.root},
        run_dir=Path(spec["run_dir"]),
        trace=trace)


def _register_knowledge_tools(mcp, spec: dict, scope: ToolScope,
                              trace: RunTrace) -> None:
    """Knowledge doc search/read + the on-demand repo_map — the same
    read-only extra tools the in-process runtime hands agent steps, rebuilt
    from the spec. Any piece that cannot be reconstructed degrades to not
    registering (capability_gap traced), never to a crash. Still absent vs
    in-process: skill_search / memory_search / candidate proposals (a
    cross-process write surface deliberately not opened here)."""
    try:
        from .engine.agent_runtime.knowledge import (
            _repo_map_tool,
            _resolve_adapter,
        )
        from .knowledge_docs import KnowledgeDocs

        ctx = _bridge_ctx(spec, scope, trace)
        adapter = _resolve_adapter(ctx)
        repo_subdir = None
        if adapter is not None:
            repo_subdir = (adapter.manifest.get("knowledge")
                           or {}).get("repo_subdir")
        if not repo_subdir and spec.get("repo"):
            repo_subdir = f"repos/{spec['repo']}"
        docs = KnowledgeDocs(ctx.settings.knowledge_dir, repo_subdir)
    except Exception as exc:  # noqa: BLE001 — degrade, never crash the bridge
        trace.record("capability_gap", capability="bridge.knowledge_docs",
                     effect=f"doc tools unavailable: {type(exc).__name__}: {exc}")
        return

    @mcp.tool(description="Search the curated knowledge base (general + this "
                          "repo's slice); returns matching doc paths.")
    def doc_search(query: str, limit: int = 20) -> str:
        trace.record("tool_call", tool="doc_search", ok=True,
                     out_of_scope=False, path=None)
        hits = docs.search(query, limit=limit)
        return "\n".join(
            f"{h.get('path')}:{h.get('line')}:{str(h.get('text') or '').strip()}"
            for h in hits) or "(no matches)"

    @mcp.tool(description="Read a knowledge doc returned by doc_search "
                          "(paged; pass the previous next_offset).")
    def doc_read(path: str, offset: int = 0) -> str:
        trace.record("tool_call", tool="doc_read", ok=True,
                     out_of_scope=False, path=path)
        page = docs.read(path, offset=offset)
        text = str(page.get("content") or "")
        nxt = page.get("next_offset")
        return text + (f"\n\n[continues — doc_read offset={nxt}]" if nxt else "")

    try:
        map_tools = _repo_map_tool(ctx, adapter)
    except Exception as exc:  # noqa: BLE001 — optional; degrade loudly
        trace.record("capability_gap", capability="bridge.repo_map",
                     effect=f"repo_map unavailable: {type(exc).__name__}: {exc}")
        return
    if "repo_map" in map_tools:
        tool = map_tools["repo_map"]

        @mcp.tool(description=tool.description)
        def repo_map(query: str) -> str:
            # dispatch with extra= mirrors the in-process extra-tool path
            # (traced, bypasses the builtin allowlist by design)
            out = dispatch("repo_map", {"query": query}, scope=scope,
                           trace=trace, extra=map_tools)
            if not out["ok"]:
                raise RuntimeError(str(out.get("error") or "tool error"))
            return str(out["result"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="infermatrix_copilot.tool_bridge",
        description="Scoped-tool MCP bridge for harness backends (stdio).")
    parser.add_argument("--spec", required=True, help="bridge spec JSON path")
    args = parser.parse_args(argv)
    try:
        server = build_server(Path(args.spec))
    except ImportError:
        import sys

        sys.stderr.write("the tool bridge needs the MCP SDK — "
                         "pip install 'infermatrix-copilot[mcp]'\n")
        return 1
    server.run()  # stdio transport by default
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
