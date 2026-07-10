"""Push authorization — the single push choke point (constraint C4).

Push safety is explicit and ANDed (plugin AND policy): a push happens only when
the PushPolicy allows it, and force-with-lease is the only force ever used —
never against a protected branch, regardless of policy. Every push in the
codebase routes through `guard_push`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PushPolicy:
    allowed: bool = False
    remote: str = "origin"
    branch: str = ""
    force_with_lease: bool = False


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
