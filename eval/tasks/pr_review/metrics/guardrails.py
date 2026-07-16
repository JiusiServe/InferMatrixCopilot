"""Release guardrails and behavioral health metrics."""

from __future__ import annotations

from ..adjudication.models import AdjudicationRow, FinalStatus
from ..benchmark.schema import BenchmarkItem
from .common import covered_gt_ids, safe_div


def merge_blocking_miss_rate(item: BenchmarkItem, rows: list[AdjudicationRow]) -> float | None:
    blocking = [finding for finding in item.gt_findings if finding.merge_blocking]
    if not blocking:
        return None
    covered = covered_gt_ids(rows)
    misses = sum(finding.id not in covered for finding in blocking)
    return misses / len(blocking)


def duplicate_rate(rows: list[AdjudicationRow]) -> float | None:
    return safe_div(sum(row.final_status == FinalStatus.DUPLICATE for row in rows), len(rows))


def adjudication_coverage(rows: list[AdjudicationRow]) -> float:
    if not rows:
        return 1.0
    unresolved = sum(row.final_status == FinalStatus.UNVERIFIABLE for row in rows)
    return 1.0 - unresolved / len(rows)
