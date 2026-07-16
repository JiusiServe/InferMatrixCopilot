"""Evaluation-health report, deliberately separated from agent quality metrics."""

from __future__ import annotations

from ..metrics.models import SummaryMetrics


def render_validity(summary: SummaryMetrics) -> str:
    status = "PROVISIONAL" if summary.provisional else "FORMAL-ELIGIBLE"
    return "\n".join([
        "# Evaluation Validity",
        "",
        f"- Status: **{status}**",
        f"- Adjudication coverage: {summary.adjudication_coverage:.2%}",
        f"- Unverifiable findings: {summary.unverifiable_finding_count}",
        f"- Benchmark-invalidated PRs: {summary.benchmark_invalidated_pr_count}",
        f"- Judge round-2 rate: {_percent(summary.judge_round2_rate)}",
        f"- Output contract failures: {summary.output_contract_failure_count}",
        f"- Benchmark version: `{summary.benchmark_version}`",
        f"- Rubric version: `{summary.rubric_version or 'unknown'}`",
        f"- Judge version: `{summary.judge_version or 'unknown'}`",
        "",
    ])


def _percent(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2%}"
