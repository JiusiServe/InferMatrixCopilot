"""ToolScope / PathScope — path-level tool permissions (design task 1).

Enforced at the single dispatch choke point (tools.dispatch). Three outcomes:
allowed; refused (tool not in scope, or write outside writable paths); allowed
but out-of-scope (write inside writable but outside the module's primary files
-> executed and recorded, never silent).
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path


@dataclass(frozen=True)
class Decision:
    """One scope ruling: `allowed` gates execution, `out_of_scope` flags an
    allowed-but-recorded write (inside writable, outside primary), and `reason`
    is the human-readable explanation used in traces and error messages."""

    allowed: bool
    out_of_scope: bool = False
    reason: str = ""


def _norm(path: str | Path) -> str:
    """Canonicalize `path` (expand `~`, resolve, posix form) so pattern matching
    is stable across cwd and symlinks."""
    return Path(path).expanduser().resolve().as_posix()


def _match_any(path: str, patterns: tuple[str, ...]) -> bool:
    """True if `path` matches any glob in `patterns`. A pattern starting with
    `*` is matched as-is (relative/suffix glob); others are normalized to an
    absolute path first."""
    return any(fnmatch(path, _norm(p) if not p.startswith("*") else p) for p in patterns)


@dataclass(frozen=True)
class PathScope:
    """Where writes may land. `writable` is a hard wall; `primary` is the
    module's owned files — writes inside writable but outside primary execute
    with an out-of-scope record."""

    writable: tuple[str, ...] = ()
    primary: tuple[str, ...] = ()

    def check_write(self, path: str | Path) -> Decision:
        """Rule on a write to `path`: refused outside `writable`; allowed-but-
        out-of-scope when inside `writable` but outside `primary` (when primary
        is set); allowed otherwise."""
        p = _norm(path)
        if not _match_any(p, self.writable):
            return Decision(False, reason=f"path outside writable scope: {p}")
        if self.primary and not _match_any(p, self.primary):
            return Decision(True, out_of_scope=True, reason=f"outside primary files: {p}")
        return Decision(True)


@dataclass(frozen=True)
class ToolScope:
    """A named permission set: which `allowed_tools` may run, an optional
    `path_scope` bounding where writes land, and `read_only` to forbid all
    writes. The unit `tools.dispatch` enforces at the single choke point."""

    name: str
    allowed_tools: frozenset[str]
    path_scope: PathScope | None = None
    read_only: bool = False

    def check(self, tool: str, write_path: str | Path | None = None) -> Decision:
        """Rule on a `tool` call: refused if the tool is not in `allowed_tools`;
        for a write (`write_path` given) also refused when read-only, else
        delegated to `path_scope`. Returns an allowed Decision otherwise."""
        if tool not in self.allowed_tools:
            return Decision(False, reason=f"tool '{tool}' not allowed in scope '{self.name}'")
        if write_path is not None:
            if self.read_only:
                return Decision(False, reason=f"scope '{self.name}' is read-only")
            if self.path_scope is not None:
                return self.path_scope.check_write(write_path)
        return Decision(True)


READ_TOOLS = frozenset({"read_file", "list_dir", "grep"})
WRITE_TOOLS = frozenset({"write_file", "edit_file"})
EXEC_TOOLS = frozenset({"run_shell"})


def read_only_scope(name: str = "read_only") -> ToolScope:
    """A scope permitting only read tools and forbidding all writes — the
    investigate/review default."""
    return ToolScope(name=name, allowed_tools=READ_TOOLS, read_only=True)


def pre_plan_scope(plan_dir: str | Path) -> ToolScope:
    """Before plan approval: read anything, write only the plan directory."""
    return ToolScope(
        name="pre_plan",
        allowed_tools=READ_TOOLS | WRITE_TOOLS,
        path_scope=PathScope(writable=(f"{_norm(plan_dir)}/*",)),
    )


def post_plan_scope(
    workspace: str | Path, extra_writable: tuple[str, ...] = (), primary: tuple[str, ...] = ()
) -> ToolScope:
    """After plan approval: write the workspace; primary files define scope."""
    writable = (f"{_norm(workspace)}/*",) + extra_writable
    return ToolScope(
        name="post_plan",
        allowed_tools=READ_TOOLS | WRITE_TOOLS | EXEC_TOOLS,
        path_scope=PathScope(writable=writable, primary=primary),
    )
