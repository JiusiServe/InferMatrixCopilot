"""Raw and severity-weighted finding recall."""

from __future__ import annotations

from ..adjudication.models import AdjudicationRow
from ..benchmark.schema import BenchmarkItem, SEVERITY_WEIGHT
from .common import covered_gt_ids, safe_div


def raw_recall(item: BenchmarkItem, rows: list[AdjudicationRow]) -> float | None:
    if not item.gt_findings:
        return None
    covered = covered_gt_ids(rows)
    return len(covered & {finding.id for finding in item.gt_findings}) / len(item.gt_findings)


def weighted_recall(item: BenchmarkItem, rows: list[AdjudicationRow]) -> float | None:
    if not item.gt_findings:
        return None
    covered = covered_gt_ids(rows)
    numerator = sum(SEVERITY_WEIGHT[f.severity] for f in item.gt_findings if f.id in covered)
    denominator = sum(SEVERITY_WEIGHT[f.severity] for f in item.gt_findings)
    return safe_div(numerator, denominator)
