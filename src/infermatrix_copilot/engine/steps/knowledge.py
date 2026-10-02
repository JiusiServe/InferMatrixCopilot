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


async def _intake_phase(ctx: StepContext, phase: str) -> StepResult:
    rt, lifecycle = _lifecycle(ctx)
    if lifecycle is None:
        return StepResult(False, FailureKind.BLOCKED, "repository is unknown or disabled")
    from ...kb_service import intake_workflow as workflow
    from ...kb_service.ledger import LeaseError
    from ...kb_service.models import ModelUnavailable
    from ...kb_service.sources import SourceError

    batch_id = str(ctx.state.get("kb_intake_batch") or "")
    try:
        if phase == "prepare":
            maximum = int(ctx.params.get("max_events", 10))
            if maximum < 1:
                return StepResult(False, FailureKind.BLOCKED, "max_events must be positive")
            batch_id = _with_lease(rt, lambda owner: workflow.prepare_intake(rt, lifecycle, owner, maximum))
            if batch_id is None and rt.ledger.events(lifecycle.repo, "pending", limit=1):
                return StepResult(False, FailureKind.BLOCKED, "pending evidence could not be prepared; see event detail")
            return StepResult(True, summary=f"prepared intake batch {batch_id or '-'}",
                              outputs={"state_updates": {"kb_intake_batch": batch_id or "",
                                                         "kb_changeset": "", "kb_changeset_status": "none"}})
        if not batch_id:
            return StepResult(True, summary="no intake batch")
        batch = workflow.load_batch(rt, batch_id)
        if batch["repo"] != lifecycle.repo:
            return StepResult(False, FailureKind.BLOCKED, "intake batch belongs to another repository")
        if phase == "draft":
            _with_lease(rt, lambda owner: workflow.draft_intake(rt, lifecycle, owner, batch_id))
            batch = workflow.load_batch(rt, batch_id)
            if batch["phase"] not in ("drafted", "complete"):
                return StepResult(False, FailureKind.BLOCKED, batch.get("error") or "intake drafting awaits review")
            return StepResult(True, summary=f"drafted intake batch {batch_id}")
        changeset_id = _with_lease(rt, lambda owner: workflow.gate_intake(rt, lifecycle, owner, batch_id))
        batch = workflow.load_batch(rt, batch_id)
        if batch["phase"] != "complete":
            return StepResult(False, FailureKind.RETRYABLE, batch.get("error") or "intake gate could not complete")
        status = rt.ledger.changeset(changeset_id)["status"] if changeset_id else "none"
        outputs = {"state_updates": {"kb_changeset": changeset_id or "", "kb_changeset_status": status}}
        held = sum(e.get("status") in ("rejected_packet", "source_unavailable", "conflicting")
                   for e in batch["events"])
        summary = f"change set {changeset_id or '-'}: {status}; {held} event(s) pending"
        if status in ("failed", "human") or not changeset_id and held:
            return StepResult(False, FailureKind.BLOCKED, summary, outputs=outputs)
        return StepResult(True, summary=summary, outputs=outputs)
    except (SourceError, LeaseError) as exc:
        return StepResult(False, FailureKind.RETRYABLE, str(exc))
    except (ModelUnavailable, ValueError, OSError) as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))


@step("knowledge.prepare_intake", kind="deterministic", risk="knowledge",
      description="Capture complete PR evidence and checkpoint one branch's owner packets")
async def prepare_intake(ctx: StepContext) -> StepResult:
    return await _intake_phase(ctx, "prepare")


@step("knowledge.draft_intake", kind="agent", risk="knowledge",
      description="Draft and checkpoint typed operations with explicit discussion coverage")
async def draft_intake(ctx: StepContext) -> StepResult:
    return await _intake_phase(ctx, "draft")


@step("knowledge.gate_intake", kind="validation", risk="knowledge",
      description="Reapply cached operations to current main, gate and stage under the writer lease")
async def gate_intake(ctx: StepContext) -> StepResult:
    return await _intake_phase(ctx, "gate")


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


def _with_lease(rt, work):
    """Run ``work(owner)`` under the single-writer lease (``kb run`` path); the
    scheduler already holds it and passes its own owner."""
    if rt.lease_owner:
        return work(rt.lease_owner)
    with rt.ledger.lease() as owner:
        return work(owner)


@step("knowledge.advance_merges", kind="deterministic", risk="knowledge",
      description="Advance in-flight knowledge PRs: sign verdicts, enqueue, record merges")
async def advance_merges(ctx: StepContext) -> StepResult:
    rt, lifecycle = _lifecycle(ctx)
    if lifecycle is None:
        return StepResult(False, FailureKind.BLOCKED, "repository is unknown or disabled")
    from ...kb_service import merge

    if rt.outbox is not None and rt.publisher_public_key is not None:
        merge.apply_acks(rt, rt.outbox.collect_acks(rt.publisher_public_key))
    events = _with_lease(rt, lambda owner: merge.advance(rt, lifecycle))
    return StepResult(True, summary="; ".join(events) or "nothing to advance",
                      outputs={"state_updates": {"kb_merge_events": events}})


@step("knowledge.sweep", kind="agent", risk="knowledge",
      description="Release sweep: T1 structure, T2/T3 rule re-checks, purge; each page through the gate")
async def sweep(ctx: StepContext) -> StepResult:
    rt, lifecycle = _lifecycle(ctx)
    if lifecycle is None or not lifecycle.full_name:
        return StepResult(False, FailureKind.BLOCKED, "repository is unknown, disabled or has no upstream")
    from ...kb_service.runtime import publish as publish_changeset
    from ...kb_service.sweep import UpstreamRepo, detect_release, run_sweep

    upstream = UpstreamRepo(rt.state_dir / "upstream" / f"{lifecycle.repo}.git", lifecycle.full_name)

    def work(owner):
        found = detect_release(rt, lifecycle, upstream)
        if found is None:
            return None
        report = run_sweep(rt, lifecycle, owner, found, upstream)
        for changeset_id in report["changesets"]:
            publish_changeset(rt, lifecycle, changeset_id)
        return report

    report = _with_lease(rt, work)
    if report is None:
        return StepResult(True, summary="no release to sweep")
    return StepResult(True, summary=f"sweep {report['sweep']['tag']}: {len(report['changesets'])} change set(s)",
                      outputs={"state_updates": {"kb_sweep_changesets": report["changesets"]}})


@step("knowledge.activate", kind="deterministic", risk="knowledge",
      description="Build, verify and activate the knowledge snapshot of the knowledge repository's main")
async def activate_snapshot(ctx: StepContext) -> StepResult:
    rt = _runtime(ctx)
    from ...kb_service.activate import ActivationError, activate

    try:
        sha = rt.knowledge.fetch()
        snapshot = activate(rt, sha)
    except ActivationError as exc:
        return StepResult(False, FailureKind.ESCALATE, f"activation refused: {exc}")
    return StepResult(True, summary=f"active snapshot {sha}",
                      outputs={"state_updates": {"kb_active_snapshot": sha, "kb_snapshot_path": str(snapshot)}})


def _init_runtime(ctx: StepContext):
    """kb init's own runtime: never the service's (that opens kb.db), and it
    serves disabled repositories — bootstrapping one is the point."""
    from pathlib import Path

    from ...kb_service.cli import DEFAULT_STATE_DIR
    from ...kb_service.init_support import InitRuntime

    return InitRuntime.from_env(ctx.settings, state_dir=Path(_STATE_DIR or DEFAULT_STATE_DIR))


@step("knowledge.init", kind="agent", risk="knowledge",
      description="kb init: bootstrap one repository's knowledge base, one human-merged stage at a time")
async def init_stage(ctx: StepContext) -> StepResult:
    from ...kb_service.init_stages import run_stage
    from ...kb_service.init_support import InitError

    repo = str(ctx.params.get("repo") or ctx.state.get("kb_repo") or "")
    stage = str(ctx.params.get("stage") or "")
    dry_run = str(ctx.params.get("dry_run", "true")).lower() not in ("0", "false", "no")
    pin = str(ctx.params.get("pin") or "") or None
    try:
        rt = _init_runtime(ctx)
        lifecycle = rt.registry.get(repo)
        if lifecycle is None:
            return StepResult(False, FailureKind.BLOCKED, f"no adapter declares knowledge repo {repo!r}")
        count = ctx.params.get("pr_count")
        kwargs = {"pr_count": int(count)} if count not in (None, "") else {}
        ceiling = ctx.params.get("budget_usd")
        if ceiling not in (None, ""):
            kwargs["budget_usd"] = float(ceiling)
        for option in ("from_existing", "subscription_generator", "retry_unfinished", "unlimited_subscription"):
            if str(ctx.params.get(option, "false")).lower() in ("1", "true", "yes"):
                kwargs[option] = True
        if ctx.params.get("acceptance_mode"):
            kwargs["acceptance_mode"] = str(ctx.params["acceptance_mode"])
        record = run_stage(rt, lifecycle, stage, dry_run=dry_run, pin=pin, **kwargs)
    except (InitError, NotImplementedError, ValueError) as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    updates = {"kb_init_stage": stage, "kb_init_status": record.status, "kb_init_pr": dict(record.pr)}
    if record.status in ("blocked", "partial"):
        return StepResult(False, FailureKind.BLOCKED, "; ".join(record.problems)[:2000] or
                          "semantic depth target unmet; partial preview and checkpoint retained",
                          outputs={"state_updates": updates})
    return StepResult(True, summary=f"kb init {stage} for {repo}: {record.status}",
                      outputs={"state_updates": updates})
