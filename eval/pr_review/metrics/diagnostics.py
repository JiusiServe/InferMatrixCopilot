"""Localization, calibration, category, inflation, and NIT diagnostics."""

from __future__ import annotations

from collections import defaultdict

from ..adjudication.models import AdjudicationRow, FinalStatus
from ..benchmark.schema import BenchmarkItem, SEVERITY_VALUE, Severity
from .common import safe_div


def localization_accuracy(item: BenchmarkItem, rows: list[AdjudicationRow]) -> float | None:
    required = {finding.id for finding in item.gt_findings if finding.location_required}
    eligible = [
        row for row in rows
        if row.final_status == FinalStatus.MATCHED_GT and row.gt_id in required
    ]
    return safe_div(sum(row.location_correct is True for row in eligible), len(eligible))


def severity_mae(rows: list[AdjudicationRow]) -> float | None:
    eligible = [
        row for row in rows
        if row.final_status == FinalStatus.MATCHED_GT and row.ground_truth_severity is not None
    ]
    if not eligible:
        return None
    return sum(
        abs(SEVERITY_VALUE[row.predicted_severity] - SEVERITY_VALUE[row.ground_truth_severity])
        for row in eligible
    ) / len(eligible)


def category_recall(item: BenchmarkItem, rows: list[AdjudicationRow]) -> dict[str, float]:
    totals: dict[str, int] = defaultdict(int)
    covered: dict[str, int] = defaultdict(int)
    gt_by_id = {finding.id: finding for finding in item.gt_findings}
    for finding in item.gt_findings:
        totals[finding.category.value] += 1
    matched_ids = {
        row.gt_id for row in rows
        if row.final_status == FinalStatus.MATCHED_GT and row.gt_id is not None
    }
    for gt_id in matched_ids:
        finding = gt_by_id.get(gt_id)
        if finding:
            covered[finding.category.value] += 1
    return {category: covered[category] / total for category, total in totals.items()}


def blocker_inflation_rate(rows: list[AdjudicationRow]) -> float | None:
    high = [row for row in rows if row.predicted_severity in {Severity.CRITICAL, Severity.BLOCKER}]
    if not high:
        return None
    inflated = 0
    for row in high:
        if row.final_status == FinalStatus.FALSE_POSITIVE:
            inflated += 1
            continue
        true_severity = row.effective_true_severity
        if true_severity is not None and SEVERITY_VALUE[true_severity] < SEVERITY_VALUE[Severity.BLOCKER]:
            inflated += 1
    return inflated / len(high)


def nit_rate(rows: list[AdjudicationRow]) -> float | None:
    valid = {FinalStatus.MATCHED_GT, FinalStatus.VALID_PARTIAL, FinalStatus.VALID_NEW}
    nit_count = sum(
        row.final_status in valid and row.effective_true_severity == Severity.NIT
        for row in rows
    )
    return safe_div(nit_count, len(rows))
