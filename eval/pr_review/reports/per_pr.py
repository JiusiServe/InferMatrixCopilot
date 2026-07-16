"""Per-PR diagnostic report."""

from __future__ import annotations

from ..metrics.models import PerPRMetrics


def render_per_pr(rows: list[PerPRMetrics]) -> str:
    lines = [
        "# Per-PR Metrics",
        "",
        "| Benchmark | Included | Recall | Weighted | Precision | Verdict | Findings | Coverage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        pct = lambda value: "N/A" if value is None else f"{value * 100:.1f}%"
        lines.append(
            f"| {row.benchmark_id} | {'yes' if row.included else 'no'} | {pct(row.raw_recall)} | "
            f"{pct(row.weighted_recall)} | {pct(row.valid_precision)} | "
            f"{'correct' if row.verdict_correct else 'wrong'} | {row.finding_count} | {pct(row.adjudication_coverage)} |"
        )
        if not row.included and row.exclusion_reason:
            lines.append(f"| ↳ exclusion |  |  |  |  | {row.exclusion_reason} |  |  |")
    return "\n".join(lines) + "\n"
