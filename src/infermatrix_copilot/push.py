"""Push authorization — the single push choke point (constraint C4).

Push safety is explicit and ANDed (adapter AND policy): a push happens only when
the PushPolicy allows it, and force-with-lease is the only force ever used —
never against a protected branch, regardless of policy. Every push in the
codebase routes through `guard_push`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PushPolicy:
    """The requested push: whether it is `allowed`, the `remote`/`branch` target,
    and whether force-with-lease is asked for. Defaults are deny-by-default
    (`allowed=False`) and non-forced. `lease_expect` optionally pins the lease
    to an exact remote SHA (`--force-with-lease=<branch>:<sha>`): after a
    history rewrite the pusher fetched the remote tip it intends to replace,
    and pinning it closes the fetch-to-push race an unqualified lease leaves
    open."""

    allowed: bool = False
    remote: str = "origin"
    branch: str = ""
    force_with_lease: bool = False
    lease_expect: str = ""
    # create-only push: the branch was observed ABSENT on the remote, and an
    # absence-pinned lease (--force-with-lease=<branch>:) guarantees the push
    # fails if anyone created it in the observe-to-push race — a plain push
    # would silently fast-forward a branch this run never saw.
    create_only: bool = False


@dataclass(frozen=True)
class PushDecision:
    """A push ruling: `allowed`, a `reason`, and the concrete git `command` to
    run when allowed (empty on deny). The command is never executed here — the
    caller runs it — so authorization and execution stay separate."""

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
    if policy.lease_expect and not policy.force_with_lease:
        return PushDecision(
            False, "lease_expect requires force_with_lease — a pinned lease "
                   "on a non-forced push signals confused intent")
    if policy.create_only and (policy.force_with_lease or policy.lease_expect):
        return PushDecision(
            False, "create_only conflicts with a lease on an existing tip — "
                   "the branch cannot be both absent and at a known SHA")
    cmd = ["git", "push", policy.remote, f"HEAD:{policy.branch}"]
    if policy.create_only:
        cmd.append(f"--force-with-lease={policy.branch}:")
    elif policy.force_with_lease:
        if policy.lease_expect:
            cmd.append(f"--force-with-lease={policy.branch}:{policy.lease_expect}")
        else:
            cmd.append("--force-with-lease")
    return PushDecision(True, "ok", tuple(cmd))
