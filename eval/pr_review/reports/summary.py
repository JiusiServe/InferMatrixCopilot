"""Human-readable Markdown summary with no synthetic composite score."""

from __future__ import annotations

from ..metrics.models import SummaryMetrics


def _pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:.2f}%"


def _num(value: float | None, digits: int = 3) -> str:
    return "N/A" if value is None else f"{value:.{digits}f}"


def render_summary(summary: SummaryMetrics) -> str:
    lines = [
        f"# PR Review Evaluation — {summary.benchmark_version}",
        "",
        f"Status: **{'PROVISIONAL' if summary.provisional else 'VALID'}**",
        f"Included PR runs: {summary.included_pr_count} (buggy {summary.buggy_pr_count}, clean {summary.clean_pr_count})",
        "",
        "## Core metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Raw Finding Recall (PR Macro) | {_pct(summary.raw_recall_macro)} |",
        f"| Raw Finding Recall (Finding Micro) | {_pct(summary.raw_recall_micro)} |",
        f"| Severity-weighted Recall (PR Macro) | {_pct(summary.weighted_recall_macro)} |",
        f"| Severity-weighted Recall (Finding Micro) | {_pct(summary.weighted_recall_micro)} |",
        f"| Valid Finding Precision (Finding Micro) | {_pct(summary.valid_finding_precision)} |",
        f"| Verdict Accuracy | {_pct(summary.verdict_accuracy)} |",
        f"| False Approve Rate | {_pct(summary.false_approve_rate)} |",
        f"| False Reject Rate | {_pct(summary.false_reject_rate)} |",
        "",
        "## Guardrails",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Merge-blocking Miss Rate | {_pct(summary.merge_blocking_miss_rate)} |",
        f"| Clean PR False-positive Rate | {_pct(summary.clean_pr_false_positive_rate)} |",
        f"| Buggy PR Empty Rate | {_pct(summary.buggy_pr_empty_rate)} |",
        f"| Duplicate Rate | {_pct(summary.duplicate_rate)} |",
        f"| Policy Violation Count | {summary.policy_violation_count} |",
        f"| Policy Violation Run Rate | {_pct(summary.policy_violation_run_rate)} |",
        f"| Tokens (input/output/cached/total) | {summary.input_tokens}/{summary.output_tokens}/{summary.cached_tokens}/{summary.total_tokens} |",
        f"| Wall Time | {summary.wall_time_ms / 1000:.2f}s |",
        f"| Tool Calls | {summary.tool_calls} |",
        "",
        "## Diagnostics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Localization Accuracy | {_pct(summary.localization_accuracy)} |",
        f"| Severity MAE | {_num(summary.severity_mae)} |",
        f"| Category Macro Recall | {_pct(summary.category_macro_recall)} |",
        f"| Blocker Inflation Rate | {_pct(summary.blocker_inflation_rate)} |",
        f"| NIT Rate | {_pct(summary.nit_rate)} |",
    ]
    if summary.category_recall:
        lines.extend(["", "### Category Recall", "", "| Category | Recall |", "|---|---:|"])
        lines.extend(f"| {category} | {_pct(value)} |" for category, value in summary.category_recall.items())
    if summary.findings_per_pr:
        d = summary.findings_per_pr
        lines.extend([
            "",
            "### Findings per PR",
            "",
            f"Mean {_num(d.mean)}, median {_num(d.median)}, P90 {_num(d.p90)}, maximum {_num(d.maximum)}.",
        ])
    lines.extend([
        "",
        "## Evaluation validity",
        "",
        f"- Adjudication Coverage: {_pct(summary.adjudication_coverage)}",
        f"- UNVERIFIABLE Findings: {summary.unverifiable_finding_count}",
        f"- Benchmark Invalidated PRs: {summary.benchmark_invalidated_pr_count}",
        f"- Judge Round-2 Rate: {_pct(summary.judge_round2_rate)}",
        f"- Output Contract Failures: {summary.output_contract_failure_count}",
        f"- Rubric Version: {summary.rubric_version or 'N/A'}",
        f"- Judge Version: {summary.judge_version or 'N/A'}",
        "",
        "No aggregate utility score is produced.",
    ])
    return "\n".join(lines) + "\n"
