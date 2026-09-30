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
