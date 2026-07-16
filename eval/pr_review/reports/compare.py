"""Side-by-side comparison that preserves each metric's direction."""

from __future__ import annotations

from ..metrics.models import SummaryMetrics


_METRICS = [
    ("raw_recall_macro", "Raw Recall", 1),
    ("weighted_recall_macro", "Weighted Recall", 1),
    ("valid_finding_precision", "Valid Precision", 1),
    ("verdict_accuracy", "Verdict Accuracy", 1),
    ("false_approve_rate", "False Approve Rate", -1),
    ("false_reject_rate", "False Reject Rate", -1),
    ("merge_blocking_miss_rate", "Merge-blocking Miss Rate", -1),
    ("duplicate_rate", "Duplicate Rate", -1),
    ("localization_accuracy", "Localization Accuracy", 1),
    ("severity_mae", "Severity MAE", -1),
    ("blocker_inflation_rate", "Blocker Inflation Rate", -1),
]


def render_compare(baseline: SummaryMetrics, candidate: SummaryMetrics) -> str:
    if baseline.benchmark_version != candidate.benchmark_version:
        raise ValueError("agent summaries must use the same benchmark version")
    lines = [
        "# PR Review Evaluation Comparison",
        "",
        f"Baseline: `{baseline.benchmark_version}`  ",
        f"Candidate: `{candidate.benchmark_version}`",
        "",
        "| Metric | Baseline | Candidate | Delta | Directional result |",
        "|---|---:|---:|---:|---|",
    ]
    for field, label, direction in _METRICS:
        before = getattr(baseline, field)
        after = getattr(candidate, field)
        if before is None or after is None:
            lines.append(f"| {label} | N/A | N/A | N/A | insufficient data |")
            continue
        delta = after - before
        directional = delta * direction
        result = "better" if directional > 1e-12 else "worse" if directional < -1e-12 else "unchanged"
        lines.append(f"| {label} | {before:.4f} | {after:.4f} | {delta:+.4f} | {result} |")
    lines.extend(["", "This table does not collapse metrics into a single score.", ""])
    return "\n".join(lines)
