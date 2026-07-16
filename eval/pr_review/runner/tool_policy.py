"""Fail-closed tool and shell-command policy for static, read-only review."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ToolDecision(StrEnum):
    ALLOW = "allow"
    REFUSE = "refuse"


@dataclass(frozen=True)
class PolicyResult:
    decision: ToolDecision
    reason: str
    violation: str | None = None


_ALLOWED_TOOLS = {
    "read_file",
    "list_directory",
    "search_text",
    "search_symbol",
    "search_references",
    "ast_query",
    "git_readonly",
}

_ALLOWED_GIT = {"diff", "show", "log", "blame", "grep", "ls-tree", "cat-file", "rev-parse"}
_DENIED_EXECUTABLES = {
    "python", "python3", "pytest", "tox", "nox", "cmake", "make", "ninja",
    "gcc", "g++", "clang", "clang++", "docker", "podman", "curl", "wget",
    "ssh", "scp", "gh", "gitlab", "pip", "uv", "poetry", "node", "npm",
    "yarn", "pnpm", "bash", "sh", "zsh", "fish",
}
_DENIED_GIT = {
    "add", "am", "apply", "bisect", "branch", "checkout", "cherry-pick", "clean",
    "clone", "commit", "fetch", "merge", "mv", "pull", "push", "rebase", "reset",
    "restore", "rm", "stash", "switch", "tag", "worktree",
}


class ToolPolicy:
    version = "pr-review-tool-policy-v0.1"

    def __init__(self, *, workspace: str | Path, allowed_commits: set[str], max_git_calls: int = 40):
        self.workspace = Path(workspace).resolve()
        self.allowed_commits = set(allowed_commits)
        self.max_git_calls = max_git_calls
        self.git_calls = 0

    def check_tool(self, tool_name: str) -> PolicyResult:
        if tool_name in _ALLOWED_TOOLS:
            return PolicyResult(ToolDecision.ALLOW, "read-only tool")
        return PolicyResult(
            ToolDecision.REFUSE,
            f"tool {tool_name!r} is not in the PR-review allowlist",
            "non_whitelisted_tool",
        )

    def check_path(self, path: str | Path) -> PolicyResult:
        candidate = Path(path)
        resolved = candidate.resolve() if candidate.is_absolute() else (self.workspace / candidate).resolve()
        try:
            resolved.relative_to(self.workspace)
        except ValueError:
            return PolicyResult(ToolDecision.REFUSE, "path escapes workspace", "hidden_data_access")
        return PolicyResult(ToolDecision.ALLOW, "path is inside workspace")

    def check_command(self, command: str) -> PolicyResult:
        try:
            argv = shlex.split(command)
        except ValueError:
            return PolicyResult(ToolDecision.REFUSE, "command cannot be parsed", "non_whitelisted_tool")
        if not argv:
            return PolicyResult(ToolDecision.REFUSE, "empty command", "non_whitelisted_tool")
        exe = Path(argv[0]).name
        if exe in _DENIED_EXECUTABLES:
            kind = "network_access" if exe in {"curl", "wget", "ssh", "scp", "gh", "gitlab"} else "code_execution"
            return PolicyResult(ToolDecision.REFUSE, f"executable {exe!r} is forbidden", kind)
        if exe != "git":
            return PolicyResult(ToolDecision.REFUSE, "only read-only git commands are accepted", "non_whitelisted_tool")
        if len(argv) < 2:
            return PolicyResult(ToolDecision.REFUSE, "missing git subcommand", "non_whitelisted_tool")
        subcommand = argv[1]
        if subcommand in _DENIED_GIT or subcommand not in _ALLOWED_GIT:
            return PolicyResult(ToolDecision.REFUSE, f"git {subcommand} is not read-only/allowed", "repository_mutation")
        if self.git_calls >= self.max_git_calls:
            return PolicyResult(ToolDecision.REFUSE, "git call budget exceeded", "tool_budget_exceeded")
        if any(token in {">", ">>", "|", "&&", ";"} for token in argv):
            return PolicyResult(ToolDecision.REFUSE, "shell composition is forbidden", "non_whitelisted_tool")

        commit_like = [arg for arg in argv[2:] if len(arg) >= 7 and all(c in "0123456789abcdefABCDEF" for c in arg)]
        unauthorized = [sha for sha in commit_like if not any(allowed.startswith(sha) or sha.startswith(allowed) for allowed in self.allowed_commits)]
        if unauthorized:
            return PolicyResult(ToolDecision.REFUSE, "command references an unauthorized commit", "review_after_commit_access")
        self.git_calls += 1
        return PolicyResult(ToolDecision.ALLOW, "allowed read-only git command")
