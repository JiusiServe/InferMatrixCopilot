"""Knowledge-service steps (``knowledge.*``) used by the kb-* playbooks.

They are thin: the logic lives in ``kb_service``; steps resolve the runtime
from the environment, act on ONE repository (``params.repo``) and publish
only plain data through ``state_updates`` so ``--resume`` works. A missing
repository, a disabled one, or an unavailable pinned model blocks the run
rather than guessing.
"""

from __future__ import annotations

from ..step import FailureKind, StepContext, StepResult
from ._common import step

_RUNTIME = None
_STATE_DIR = None


def use_state_dir(state_dir) -> None:
    """Pin the state directory the steps' runtime uses (``kb --state-dir``)."""
    global _RUNTIME, _STATE_DIR
    if _STATE_DIR != state_dir:
        _STATE_DIR, _RUNTIME = state_dir, None


def _runtime(ctx: StepContext):
    global _RUNTIME
    if _RUNTIME is None:
        from ...kb_service.runtime import KbRuntime

        _RUNTIME = KbRuntime.from_env(ctx.settings, state_dir=_STATE_DIR)
    return _RUNTIME


def _lifecycle(ctx: StepContext):
    rt = _runtime(ctx)
    repo = str(ctx.params.get("repo") or ctx.state.get("kb_repo") or "")
    lifecycle = rt.registry.get(repo)
    if lifecycle is None or not lifecycle.enabled:
        return rt, None
    return rt, lifecycle


@step("knowledge.collect_events", kind="deterministic", risk="read",
      description="Record new knowledge events (merged PRs, Copilot run lessons) for one repository")
async def collect_events(ctx: StepContext) -> StepResult:
    rt, lifecycle = _lifecycle(ctx)
    if lifecycle is None:
        return StepResult(False, FailureKind.BLOCKED, "repository is unknown or disabled")
    from ...kb_service.runtime import collect_events as collect

    count = collect(rt, lifecycle)
    return StepResult(True, summary=f"{count} new event(s)",
                      outputs={"state_updates": {"kb_repo": lifecycle.repo, "kb_new_events": count}})


@step("knowledge.intake", kind="agent", risk="knowledge",
      description="Draft typed knowledge operations from pending events and run the quality gate")
async def intake(ctx: StepContext) -> StepResult:
    rt, lifecycle = _lifecycle(ctx)
    if lifecycle is None:
        return StepResult(False, FailureKind.BLOCKED, "repository is unknown or disabled")
    from ...kb_service.runtime import run_intake

    changeset_id = run_intake(rt, lifecycle, max_events=int(ctx.params.get("max_events", 10)))
    status = rt.ledger.changeset(changeset_id)["status"] if changeset_id else "none"
    return StepResult(True, summary=f"change set {changeset_id or '-'}: {status}",
                      outputs={"state_updates": {"kb_changeset": changeset_id or "",
                                                 "kb_changeset_status": status}})


@step("knowledge.publish", kind="deterministic", risk="knowledge",
      description="Hand a gated change set to the publisher (auto_merge) or record it (shadow)")
async def publish(ctx: StepContext) -> StepResult:
    rt, lifecycle = _lifecycle(ctx)
    changeset_id = str(ctx.state.get("kb_changeset") or "")
    if lifecycle is None:
        return StepResult(False, FailureKind.BLOCKED, "repository is unknown or disabled")
    if not changeset_id:
        return StepResult(True, summary="nothing to publish")
    from ...kb_service.runtime import publish as publish_changeset

    status = publish_changeset(rt, lifecycle, changeset_id)
    return StepResult(True, summary=f"change set {changeset_id}: {status}",
                      outputs={"state_updates": {"kb_changeset_status": status}})
