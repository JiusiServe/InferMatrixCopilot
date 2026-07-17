"""Outward-writing PR steps (risk=push): the guarded push and the gated review
comment. Both are the choke points the safety model governs — `ci.push` runs
through `guard_push` (PushPolicy AND protected branches, dry-run by default) and
`pr.post_review` is built from the shared `post_step` factory (explicit post
flag + ALLOW_POST).
"""

from __future__ import annotations

import subprocess

from ....push import PushPolicy, guard_push
from ...step import FailureKind, StepContext, StepResult, StepSpec
from .._common import register_step, step
from .._common import post_step as _post_step
from .._common import repo_path as _repo_path


@step("ci.push", "script", "push",
      "Guarded push (PushPolicy AND protected branches; dry-run default).")
async def _push(ctx: StepContext) -> StepResult:
    """The single C4 push choke point: authorize a git push through `guard_push`
    (PushPolicy AND protected branches) before ever running it. Rehydrates the
    `push_policy` from state (dict or PushPolicy) and the protected-branch list
    from state or settings.

    A denied decision returns FORBIDDEN. When authorized but `ALLOW_PUSH=0`
    (the default), it stays a dry run — reports the command it *would* run, never
    executes. Only with pushes enabled does it run the git command; a non-zero
    exit returns ESCALATE with the stderr tail."""
    repo = _repo_path(ctx)
    raw = ctx.state.get("push_policy")
    policy = raw if isinstance(raw, PushPolicy) else PushPolicy(**(raw or {}))
    protected = ctx.state.get("protected_branches") or ctx.settings.protected_branches
    ctx.trace.record("push_requested", remote=policy.remote, branch=policy.branch)
    decision = guard_push(policy, list(protected))
    if not decision.allowed:
        return StepResult(False, FailureKind.FORBIDDEN, decision.reason)
    if not ctx.settings.allow_push:
        return StepResult(True, summary=f"dry-run (ALLOW_PUSH=0): {' '.join(decision.command)}",
                          outputs={"dry_run": True, "command": list(decision.command)})
    out = subprocess.run(list(decision.command), cwd=str(repo), capture_output=True,
                         text=True, encoding="utf-8", errors="replace", timeout=300)
    if out.returncode != 0:
        return StepResult(False, FailureKind.ESCALATE,
                          f"push failed: {out.stderr[-1_000:]}")
    return StepResult(True, summary=f"pushed {policy.remote} HEAD:{policy.branch}")


register_step(StepSpec(
    "pr.post_review", "script", "push",
    _post_step("review_text",
               lambda spec, body: ["pr", "comment", str(spec.get("pr")),
                                    "--body", body],
               "PR review comment"),
    "Post the review as a PR comment (explicit post flag + ALLOW_POST)."))
