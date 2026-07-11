"""Reporting step: RUN_REPORT.md from accumulated step outputs."""

from __future__ import annotations

from ..step import StepContext, StepResult
from ._common import step

# The user-facing artifacts a run produces: rendered FIRST and IN FULL.
# Everything else is per-step diagnostics, truncated. (The old renderer
# truncated every value at 2k chars — judged reviews ended mid-word.)
_DELIVERABLE_KEYS = ("review_text", "draft_answer", "triage_table")


@step("report.final_summary", "report", "report",
      "Write RUN_REPORT.md from accumulated step outputs.")
async def _final_report(ctx: StepContext) -> StepResult:
    """Write RUN_REPORT.md into the run dir: the run's deliverables
    (review/answer/triage) first and untruncated, then one diagnostics section
    per step with values truncated (`state_updates` plumbing is skipped — it
    duplicates the deliverables and dumps raw diffs). Returns the report path
    in `outputs["report"]`."""
    lines = ["# Run report", ""]
    spec = ctx.state.get("task_spec")
    if spec:
        lines += [f"- task: {spec}", ""]
    outputs_map = ctx.state.get("outputs") or {}
    for step_id, outputs in outputs_map.items():
        for key in _DELIVERABLE_KEYS:
            text = (outputs or {}).get(key) or ctx.state.get(key)
            if text:
                lines += [f"## {key}", "", str(text), ""]
                break
    lines += ["---", "", "## Step diagnostics", ""]
    for step_id, outputs in outputs_map.items():
        lines.append(f"### {step_id}")
        for k, v in (outputs or {}).items():
            if k in _DELIVERABLE_KEYS or k == "state_updates":
                continue
            lines.append(f"- **{k}**: {str(v)[:2_000]}")
        lines.append("")
    path = ctx.run_dir / "RUN_REPORT.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return StepResult(True, summary=f"report written: {path}",
                      outputs={"report": str(path)})
