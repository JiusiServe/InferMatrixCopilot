"""Reporting step: RUN_REPORT.md from accumulated step outputs."""

from __future__ import annotations

from ..step import StepContext, StepResult
from ._common import step


@step("report.final_summary", "report", "report",
      "Write RUN_REPORT.md from accumulated step outputs.")
async def _final_report(ctx: StepContext) -> StepResult:
    lines = ["# Run report", ""]
    spec = ctx.state.get("task_spec")
    if spec:
        lines += [f"- task: {spec}", ""]
    for step_id, outputs in (ctx.state.get("outputs") or {}).items():
        lines.append(f"## {step_id}")
        for k, v in (outputs or {}).items():
            lines.append(f"- **{k}**: {str(v)[:2_000]}")
        lines.append("")
    path = ctx.run_dir / "RUN_REPORT.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return StepResult(True, summary=f"report written: {path}",
                      outputs={"report": str(path)})
