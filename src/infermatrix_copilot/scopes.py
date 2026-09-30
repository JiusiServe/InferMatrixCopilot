"""ToolScope / PathScope — path-level tool permissions (design task 1).

Enforced at the single dispatch choke point (tools.dispatch). Three outcomes:
allowed; refused (tool not in scope, or write outside writable paths); allowed
but out-of-scope (write inside writable but outside the module's primary files
-> executed and recorded, never silent).
"""

from __future__ import annotations

import os
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
    root: str = ""  # repo root: RELATIVE tool paths resolve against it (the
                    # agent works in repo-relative paths — e.g. from the diff —
                    # while the actual tree may be a per-PR worktree it can't
                    # hardcode). Empty = resolve against process cwd (legacy).
    # Shadow-run fences (meta-improvement design §8.2). All default to "off",
    # which is exactly today's behaviour.
    read_roots: tuple[str, ...] = ()     # when set, every READ/exec path must
                                         # realpath under one of these (symlinks
                                         # and `..` resolved first)
    deny_prefixes: tuple[str, ...] = ()  # realpath prefixes always refused
                                         # (a `--shared` clone's .git/)
    strict_extras: bool = False          # step-provided extras must be in
                                         # allowed_tools; internal-write extras
                                         # are refused outright
    executables: tuple[str, ...] = ()    # the shadow PATH whitelist (enforced by
                                         # the shadow environment; recorded here
                                         # so the scope is self-describing)

    def check_read(self, path: str | Path) -> Decision:
        """Rule on a read/exec path: allowed unless `read_roots` is set and the
        resolved path (symlinks and `..` followed) lies outside every root or
        under a denied prefix."""
        if not self.read_roots:
            return Decision(True)
        real = os.path.realpath(str(path))
        for prefix in self.deny_prefixes:
            p = os.path.realpath(prefix)
            if real == p or real.startswith(p + os.sep):
                return Decision(False, reason=f"path under a denied prefix: {real}")
        for root in self.read_roots:
            r = os.path.realpath(root)
            if real == r or real.startswith(r + os.sep):
                return Decision(True)
        return Decision(False, reason=f"path outside read roots of scope '{self.name}': {real}")

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


def shadow_scope(shadow_dir: str | Path, *, tools: tuple[str, ...] | frozenset[str] = (),
                 extra_read_roots: tuple[str, ...] = (), executables: tuple[str, ...] = (),
                 name: str = "shadow") -> ToolScope:
    """The scope of a shadow (experiment) run: builtin read tools plus the
    workflow's declared shadow tools, read-only, every read confined to the
    shadow checkout (and the read-only knowledge/adapter roots), the clone's
    `.git/` denied (a `--shared` clone's alternates file names the source
    repository's object store), extras enforced strictly."""
    root = _norm(shadow_dir)
    return ToolScope(
        name=name, allowed_tools=READ_TOOLS | frozenset(tools), read_only=True, root=root,
        read_roots=(root, *(_norm(r) for r in extra_read_roots)),
        deny_prefixes=(f"{root}/.git",), strict_extras=True, executables=tuple(executables))
