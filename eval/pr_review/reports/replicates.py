"""Formal repeated-run statistics (mean, sample standard deviation, raw values)."""

from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Any

from ..metrics.models import PerPRMetrics, SummaryMetrics


SUMMARY_FIELDS = (
    "raw_recall_macro",
    "raw_recall_micro",
    "weighted_recall_macro",
    "weighted_recall_micro",
    "valid_finding_precision",
    "verdict_accuracy",
    "false_approve_rate",
    "false_reject_rate",
    "merge_blocking_miss_rate",
    "clean_pr_false_positive_rate",
    "buggy_pr_empty_rate",
    "duplicate_rate",
    "localization_accuracy",
    "severity_mae",
    "category_macro_recall",
    "blocker_inflation_rate",
    "nit_rate",
    "adjudication_coverage",
)

PER_PR_FIELDS = (
    "raw_recall",
    "weighted_recall",
    "valid_precision",
    "finding_count",
    "localization_accuracy",
    "severity_mae",
)


def _stats(values: list[float]) -> dict[str, Any]:
    return {
        "mean": statistics.fmean(values),
        "standard_deviation": statistics.stdev(values) if len(values) >= 2 else 0.0,
        "raw": values,
    }


def summarize_replicates(
    summaries: list[SummaryMetrics],
    per_pr_runs: list[list[PerPRMetrics]] | None = None,
) -> dict[str, Any]:
    if not summaries:
        raise ValueError("at least one run summary is required")
    versions = {summary.benchmark_version for summary in summaries}
    if len(versions) != 1:
        raise ValueError("replicate summaries must use the same benchmark version")
    result: dict[str, Any] = {
        "benchmark_version": summaries[0].benchmark_version,
        "run_count": len(summaries),
        "metrics": {},
        "raw_runs": [summary.model_dump(mode="json", exclude_none=True) for summary in summaries],
    }
    for field in SUMMARY_FIELDS:
        values = [float(value) for summary in summaries if (value := getattr(summary, field)) is not None]
        if values:
            result["metrics"][field] = _stats(values)
    if per_pr_runs is not None:
        by_pr: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        for run in per_pr_runs:
            for row in run:
                if not row.included:
                    continue
                for field in PER_PR_FIELDS:
                    value = getattr(row, field)
                    if value is not None:
                        by_pr[row.benchmark_id][field].append(float(value))
        result["per_pr_distribution"] = {
            benchmark_id: {field: _stats(values) for field, values in fields.items()}
            for benchmark_id, fields in sorted(by_pr.items())
        }
    return result
