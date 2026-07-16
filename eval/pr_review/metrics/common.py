"""Shared metric helpers."""

from __future__ import annotations

from collections.abc import Iterable

from ..adjudication.models import AdjudicationRow, FinalStatus
from ..benchmark.schema import BenchmarkItem


def safe_div(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def rows_by_prediction(rows: list[AdjudicationRow]) -> dict[str, AdjudicationRow]:
    result: dict[str, AdjudicationRow] = {}
    for row in rows:
        if row.prediction_id in result:
            raise ValueError(f"duplicate adjudication row for prediction {row.prediction_id}")
        result[row.prediction_id] = row
    return result


def validate_adjudication_coverage(prediction_ids: Iterable[str], rows: list[AdjudicationRow]) -> None:
    expected = set(prediction_ids)
    actual = {row.prediction_id for row in rows}
    if expected != actual:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"adjudication rows mismatch predictions; missing={missing}, extra={extra}")
    matched_gt_ids = [
        row.gt_id for row in rows
        if row.final_status == FinalStatus.MATCHED_GT and row.gt_id is not None
    ]
    if len(matched_gt_ids) != len(set(matched_gt_ids)):
        raise ValueError("MATCHED_GT adjudications violate one-to-one GT matching")


def covered_gt_ids(rows: list[AdjudicationRow]) -> set[str]:
    return {
        row.gt_id
        for row in rows
        if row.final_status == FinalStatus.MATCHED_GT and row.gt_id is not None
    }


def gt_map(item: BenchmarkItem):
    return {finding.id: finding for finding in item.gt_findings}
