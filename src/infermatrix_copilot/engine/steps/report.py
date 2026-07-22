"""Reporting step: RUN_REPORT.md (deliverables only) + DIAGNOSTICS.md."""

from __future__ import annotations

from pathlib import Path

from ..step import StepContext, StepResult
from ._common import step

# The user-facing artifacts a run produces — RUN_REPORT.md contains each
# exactly ONCE and nothing else (T3 forensics #1: the per-step fallback loop
# triplicated review_text in 15/15 reports and leaked truncated diagnostics
# copies + blockers/confidence arrays into the judged artifact).
_DELIVERABLE_KEYS = ("review_text", "draft_answer", "triage_table")
# raw agent-contract fields that duplicate deliverables or leak internal state
_DIAG_SKIP = set(_DELIVERABLE_KEYS) | {"state_updates", "answer_draft",
                                       "review_comments"}


@step("report.final_summary", "report", "report",
      "Write RUN_REPORT.md (deliverables) + DIAGNOSTICS.md (step outputs).")
async def _final_report(ctx: StepContext) -> StepResult:
    """Write RUN_REPORT.md with each deliverable exactly once (state first —
    it always holds the full text — then step outputs), plus the checkout note
    and the skill-curation queue. Per-step diagnostics go to DIAGNOSTICS.md in
    the run dir, never into the deliverable. Returns the report path."""
    lines = ["# Run report", ""]
    spec = ctx.state.get("task_spec")
    if spec:
        lines += [f"- task: {spec}", ""]
    note = ctx.state.get("checkout_note")
    if note:
        lines += [f"- {note}", ""]
    outputs_map = ctx.state.get("outputs") or {}
    for key in _DELIVERABLE_KEYS:
        text = ctx.state.get(key)
        if not text:
            for outputs in outputs_map.values():
                if (outputs or {}).get(key):
                    text = outputs[key]
                    break
        if text:
            lines += [f"## {key}", "", str(text), ""]
    try:  # surface proposed-but-unpromoted skills — the curation queue was silent
        from ...memory.skills import SkillStore
        from ..agent_runtime.knowledge import _resolve_adapter

        stores = [SkillStore(ctx.settings.skills_dir)]
        adapter = _resolve_adapter(ctx)
        if adapter is not None and adapter.skills_dir != Path(ctx.settings.skills_dir):
            stores.insert(0, SkillStore(adapter.skills_dir))
        cands = {n: c for st in stores for n, c in st.candidates().items()}
        if cands:
            lines += ["## skill candidates awaiting curation", ""]
            lines += [f"- **{n}**: {str(c.get('description', ''))[:200]}"
                      for n, c in sorted(cands.items())]
            lines += ["", "(promote with SkillStore.promote(name); candidates "
                      "are never auto-activated)", ""]
    except Exception:  # noqa: BLE001 — reporting must never fail the run
        pass
    diag = ["# Step diagnostics", ""]
    for step_id, outputs in outputs_map.items():
        diag.append(f"## {step_id}")
        for k, v in (outputs or {}).items():
            if k in _DIAG_SKIP:
                continue
            diag.append(f"- **{k}**: {str(v)[:2_000]}")
        diag.append("")
    (ctx.run_dir / "DIAGNOSTICS.md").write_text("\n".join(diag), encoding="utf-8")
    path = ctx.run_dir / "RUN_REPORT.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return StepResult(True, summary=f"report written: {path}",
                      outputs={"report": str(path)})
