"""Meta-improvement engine steps.

`improve.stage_items` runs BEFORE shadow isolation, in the engine's own
scope: it stages every pre-registered item (`repo#pr@head`) into a snapshot
plus an independent shadow clone (design §8.2) and publishes them so a
`pr_context_source=snapshot` run consumes them without touching the network.
"""

from __future__ import annotations

from pathlib import Path

from ..step import FailureKind, StepContext, StepResult
from ._common import step


@step("improve.stage_items", "deterministic", "read",
      "Stage pre-registered PR items into snapshots + shadow clones (pre-isolation).")
async def _stage_items(ctx: StepContext) -> StepResult:
    """Items come from `params.items` (a list or a comma-separated string) or
    `state['improve_items']`. Every item is staged or the step fails: an
    experiment whose inputs are partly approximated is invalid by design.

    Publishes `pr_snapshots` ({item: snapshot}) and, for a single item,
    `pr_snapshot` (what the snapshot-mode PR steps read)."""
    from ...improve.staging import StagingError, stage_item

    raw = ctx.params.get("items") or ctx.state.get("improve_items") or []
    if isinstance(raw, str):
        raw = [x for x in raw.split(",") if x.strip()]
    items = [str(x).strip() for x in raw if str(x).strip()]
    if not items:
        return StepResult(False, FailureKind.BLOCKED, "no items to stage (params.items / state.improve_items)")
    shadow_root = Path(ctx.params.get("shadow_root") or (ctx.run_dir / "shadow"))
    snapshots: dict[str, dict] = {}
    for item in items:
        try:
            snapshots[item] = stage_item(ctx, item, shadow_root=shadow_root)
        except StagingError as exc:
            ctx.trace.record("item_staging_failed", item=item, reason=str(exc)[:300])
            return StepResult(False, FailureKind.BLOCKED, f"staging failed for {item}: {exc}")
    updates: dict = {"pr_snapshots": snapshots}
    if len(snapshots) == 1:
        updates["pr_snapshot"] = next(iter(snapshots.values()))
    ctx.state.update(updates)
    return StepResult(True, summary=f"staged {len(snapshots)} item(s) under {shadow_root}",
                      outputs={"staged": sorted(snapshots), "state_updates": updates})


def _ledger_dir(ctx: StepContext) -> Path:
    from ...improve.cycle import ledger_dir_for

    override = str(ctx.params.get("ledger_dir") or "")
    return Path(override).expanduser() if override else ledger_dir_for(ctx.settings)


def _trace_store(ctx: StepContext):
    from ...trace_store import TraceStore, current_store

    store = current_store()
    if store is not None:
        return store
    root = str(getattr(ctx.settings, "trace_store_root", "") or "")
    if not root:
        return None
    return TraceStore(Path(root).expanduser())


@step("improve.preflight", "deterministic", "read",
      "Kill switch + per-workflow holds; refuses the cycle loudly.")
async def _preflight(ctx: StepContext) -> StepResult:
    from ...improve.cycle import CycleRefused, preflight
    from ...improve.ledger import Ledger

    store = _trace_store(ctx)
    if store is None:
        return StepResult(False, FailureKind.BLOCKED, "no trace store (set TRACE_STORE_ROOT)")
    try:
        gate = preflight(ctx.settings, Ledger(_ledger_dir(ctx), store))
    except CycleRefused as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    updates = {"improve_holds": gate["holds"], "improve_ledger_dir": str(_ledger_dir(ctx))}
    ctx.state.update(updates)
    return StepResult(True, summary=f"preflight ok; holds: {gate['holds'] or 'none'}",
                      outputs={"state_updates": updates})


@step("improve.lint", "deterministic", "read",
      "Tier 1 lints + baselines + ledger update over the cycle window (dry-run).")
async def _lint(ctx: StepContext) -> StepResult:
    """Runs the whole P1 cycle body (lints, baselines, Tier 1 proposals in
    the ledger, stale sweep, report). Window from params `since`/`until`
    (epoch seconds) or the cursor. Publishes `improve_report_path`."""
    from ...improve.cycle import CycleRefused, run_cycle

    store = _trace_store(ctx)
    if store is None:
        return StepResult(False, FailureKind.BLOCKED, "no trace store (set TRACE_STORE_ROOT)")
    since = ctx.params.get("since")
    until = ctx.params.get("until")
    try:
        report = run_cycle(store, ctx.settings, _ledger_dir(ctx),
                           since=float(since) if since else None, until=float(until) if until else None,
                           dry_run=True, force=bool(ctx.params.get("force")))
    except CycleRefused as exc:
        return StepResult(False, FailureKind.BLOCKED, str(exc))
    updates = {"improve_cycle": {k: report[k] for k in ("at", "since", "until", "units", "proposals_opened")},
               "improve_report_dir": str(_ledger_dir(ctx) / "reports")}
    ctx.state.update(updates)
    opened = len(report["proposals_opened"])
    return StepResult(True, summary=f"cycle over {report['units']} units in {len(report['workflows'])} workflow(s); "
                                    f"{opened} Tier 1 proposal(s) opened (dry-run)",
                      outputs={"report": report, "state_updates": updates})


@step("improve.ledger", "deterministic", "read",
      "Summarize the per-workflow ledgers for the run report.")
async def _ledger_summary(ctx: StepContext) -> StepResult:
    from ...improve.ledger import Ledger

    ledger = Ledger(_ledger_dir(ctx))
    lines = []
    for workflow in ledger.workflows():
        wl = ledger.load(workflow)
        open_ = [p for p in wl.proposals if p.state not in ("landed", "closed")]
        last = wl.cycles[-1] if wl.cycles else {}
        lines.append(f"{workflow}: tier {wl.tier}, {len(wl.cycles)} cycle(s), last units {last.get('units', 0)}, "
                     f"{len(open_)} live proposal(s)" + (f", HOLD: {wl.hold}" if wl.hold else ""))
    summary = "\n".join(lines) or "no workflows in the ledger yet"
    return StepResult(True, summary=summary[:400], outputs={"ledger_summary": summary})
