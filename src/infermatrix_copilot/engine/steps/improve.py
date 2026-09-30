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


def _forensics_agents(ctx: StepContext) -> dict:
    """Two investigator families from the configured tiers (eco and, when
    configured, performance); one family only when that is all there is —
    the report then says `single_family`."""
    from ...agent_loop import run_agent

    if ctx.llm is None or not getattr(ctx.llm, "available", False):
        return {}
    agents = {}
    for mode in ("eco", "performance"):
        try:
            target = ctx.settings.tier_target(mode)
        except Exception:  # noqa: BLE001 - an unconfigured tier is simply absent
            continue
        family = f"{target.provider_id or target.source}:{target.model}"
        if family in agents:
            continue
        llm = ctx.llm.for_target(target) if hasattr(ctx.llm, "for_target") else ctx.llm

        def make(llm_=llm, model_=target.model):
            def agent(system, prompt, scope, extra_tools, max_iters):
                return run_agent(llm_, system=system, prompt=prompt, scope=scope, trace=ctx.trace,
                                 model=model_, max_iters=max_iters, extra_tools=extra_tools).text
            return agent
        agents[family] = make()
    return agents


@step("improve.forensics", "agent", "read",
      "Tier 2: coverage matrices + stage-of-loss attribution for workflows with an outcome adapter.")
async def _forensics(ctx: StepContext) -> StepResult:
    """For each Tier 2 workflow in the last cycle's window: import outcomes,
    build the gold × unit matrix, attribute every miss with two agent
    families, rank the punch list. Params: `workflow` (restrict), `max_cells`.
    Publishes `improve_forensics` (punch lists + measurement health)."""
    from ...improve.adapters import load_adapter
    from ...improve.enroll import declarations_for
    from ...improve.forensics import attribute, coverage_matrix, measurement_health, punch_list, unit_scores
    from ...improve.reader import collect_units
    from ...trace_store import bind_store, trace_context

    store = _trace_store(ctx)
    if store is None:
        return StepResult(False, FailureKind.BLOCKED, "no trace store (set TRACE_STORE_ROOT)")
    cycle = ctx.state.get("improve_cycle") or {}
    since, until = cycle.get("since"), cycle.get("until")
    if since is None or until is None:
        return StepResult(False, FailureKind.BLOCKED, "improve.forensics needs the cycle window (run improve.lint first)")
    only = str(ctx.params.get("workflow") or "")
    decls = declarations_for(ctx.settings)
    agents = _forensics_agents(ctx)
    results: dict = {}
    with bind_store(store), trace_context(playbook="workflow-improve", run_id=ctx.run_dir.name):
        units, _ = collect_units(store, float(since), float(until))
        for name, decl in decls.items():
            if not decl.tier2 or (only and name != only):
                continue
            wf_units = [u for u in units.values() if u.workflow == name]
            if len(wf_units) < decl.tier2_min_items and not ctx.params.get("force"):
                results[name] = {"skipped": f"{len(wf_units)} units < tier2_min_items {decl.tier2_min_items}"}
                continue
            adapter = load_adapter(decl.outcome_adapter, **_adapter_kwargs(ctx, decl))
            collected = _collect_outcomes(ctx, adapter, wf_units, store)
            outcomes: dict = {}
            cells, golds = coverage_matrix(adapter, wf_units, store, outcomes=outcomes)
            scored = unit_scores(adapter, wf_units, outcomes, golds)
            entry: dict = {"units": len(wf_units), "cells": len(cells), "collected": collected,
                           "outcomes": len(outcomes), "finding_labels": scored["findings"],
                           "scores": scored["units"],
                           "misses": sum(1 for c in cells if c.status == "miss"),
                           "unlabeled": sum(1 for c in cells if c.status == "unlabeled"),
                           "descriptive_only": bool(getattr(adapter, "descriptive_only", False)),
                           "families": sorted(agents), "single_family": len(agents) < 2}
            if cells and agents:
                attributions = attribute(store, {u.unit_id: u for u in wf_units}, golds, cells, agents=agents,
                                         max_cells=int(ctx.params.get("max_cells") or 40))
                entry["punch_list"] = punch_list(attributions, golds, {u.unit_id: u for u in wf_units})
                entry["measurement"] = measurement_health(attributions)
            elif cells and not agents:
                entry["skipped"] = "no LLM configured for the forensics agents"
            results[name] = entry
    ctx.state["improve_forensics"] = results
    done = [n for n, r in results.items() if "punch_list" in r]
    return StepResult(True, summary=f"forensics: {len(done)} workflow(s) attributed, "
                                    f"{sum(1 for r in results.values() if 'skipped' in r)} skipped",
                      outputs={"forensics": results, "state_updates": {"improve_forensics": results}})


def _adapter_kwargs(ctx: StepContext, decl) -> dict:
    """Construction arguments per adapter, from settings/params (never
    secrets): the eval adapter needs the GT and judgment dirs and the arm
    name; the bot adapter needs nothing."""
    if decl.outcome_adapter.endswith(":ReviewEvalAdapter"):
        return {"gt_dir": str(ctx.params.get("gt_dir") or getattr(ctx.settings, "improve_gt_dir", "") or "eval/dataset/gt"),
                "judgments_dir": ctx.params.get("judgments_dir") or getattr(ctx.settings, "improve_judgments_dir", "") or None,
                "arm": str(ctx.params.get("arm") or getattr(ctx.settings, "improve_eval_arm", "") or "")}
    if decl.outcome_adapter.endswith(":RbReviewAdapter"):
        return {"bot_login": str(getattr(ctx.settings, "improve_rb_bot_login", "") or "")}
    return {}


def _judge_spec(ctx: StepContext):
    """The gold_match judge from settings.improve_judge: "api:<model>" or
    "cli:<provider>:<model>"; None when unset (cells stay unlabeled and the
    report says so)."""
    from ...improve.judges import JudgeSpec

    raw = str(ctx.params.get("judge") or getattr(ctx.settings, "improve_judge", "") or "")
    if not raw:
        return None
    parts = raw.split(":")
    if parts[0] == "api" and len(parts) == 2:
        return JudgeSpec("api", parts[1])
    if parts[0] == "cli" and len(parts) == 3:
        return JudgeSpec("cli", parts[2], provider=parts[1])
    raise ValueError(f"improve_judge must be api:<model> or cli:<provider>:<model>, got {raw!r}")


def _collect_outcomes(ctx: StepContext, adapter, units, store) -> dict:
    """Outcome collection BEFORE the matrix: the bot adapter fetches thread
    labels inside fetch(); the eval adapter imports the paired judge's
    verdicts and, when a judge is configured, decides every undecided gold
    entry with gold_match. Nothing here is fabricated: without a judge the
    cells stay unlabeled and the report counts them."""
    from ...improve.adapters.review_eval import ReviewEvalAdapter
    from ...improve.judges import JudgeError

    summary = {"verdicts": 0, "gold_matched": 0, "judge": "", "errors": []}
    if not isinstance(adapter, ReviewEvalAdapter):
        return summary
    judge = _judge_spec(ctx)
    if judge is not None:
        adapter.judge = judge
        adapter.llm = ctx.llm if judge.kind == "api" else None
        adapter.governor = getattr(ctx, "governor", None)
        summary["judge"] = f"{judge.kind}:{judge.provider + ':' if judge.provider else ''}{judge.model}"
    for unit in units:
        try:
            summary["verdicts"] += adapter.collect_judge_verdicts(unit, store)
        except Exception as exc:  # noqa: BLE001 - one bad judgment file must not stop the rest
            summary["errors"].append(f"{unit.unit_id}: verdicts: {exc}"[:200])
        gold = adapter.gold(unit.item)
        if gold is None or judge is None:
            continue
        try:
            summary["gold_matched"] += adapter.gold_match(unit, gold, store)
        except JudgeError as exc:
            summary["errors"].append(f"{unit.unit_id}: gold_match: {exc}"[:200])
    summary["inconclusive"] = len(getattr(adapter, "inconclusive", []) or [])
    return summary
