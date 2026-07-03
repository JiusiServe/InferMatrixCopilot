"""Target-layer data structures (DESIGN_REBASE_TARGET) + the unified push guard.

Push safety is explicit and ANDed (plugin AND policy): a push happens only when
the PushPolicy allows it, and force-with-lease is the only force ever used —
never against a protected branch, regardless of policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class PushPolicy:
    allowed: bool = False
    remote: str = "origin"
    branch: str = ""
    force_with_lease: bool = False


@dataclass
class ValidationPlan:
    local_tests: list[str] = field(default_factory=list)
    ci_pipelines: list[str] = field(default_factory=list)
    precommit: bool = True


@dataclass
class ModuleTask:
    module: str
    agent_mode: Literal["rebase", "verify", "compat_check", "review_only"] = "rebase"
    files: list[str] = field(default_factory=list)
    test_commands: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class ModuleSchedule:
    waves: list[list[ModuleTask]] = field(default_factory=list)


@dataclass
class RebaseRunSpec:
    kind: str = "repo_rebase"
    repo_path: str = ""
    base_ref: str = "origin/main"
    head_ref: str = ""


@dataclass(frozen=True)
class PushDecision:
    allowed: bool
    reason: str
    command: list[str] = ()


def guard_push(policy: PushPolicy, protected_branches: list[str]) -> PushDecision:
    """The single choke point every push step must pass."""
    if not policy.allowed:
        return PushDecision(False, "push not allowed by PushPolicy")
    if not policy.branch:
        return PushDecision(False, "push branch not set")
    if policy.branch in protected_branches:
        if policy.force_with_lease:
            return PushDecision(
                False, f"force-push to protected branch '{policy.branch}' is forbidden"
            )
        return PushDecision(
            False,
            f"direct push to protected branch '{policy.branch}' is forbidden — deliver via PR",
        )
    cmd = ["git", "push", policy.remote, f"HEAD:{policy.branch}"]
    if policy.force_with_lease:
        cmd.append("--force-with-lease")
    return PushDecision(True, "ok", tuple(cmd))
