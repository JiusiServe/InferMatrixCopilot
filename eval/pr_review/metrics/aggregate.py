"""Deterministic per-PR and benchmark-wide metric aggregation."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict

from ..adjudication.models import FinalStatus
from ..benchmark.schema import CleanStatus, SEVERITY_VALUE, SEVERITY_WEIGHT, Severity, Verdict
from .common import covered_gt_ids, safe_div, validate_adjudication_coverage
from .diagnostics import (
    blocker_inflation_rate,
    category_recall,
    localization_accuracy,
    nit_rate,
    severity_mae,
)
from .guardrails import adjudication_coverage, duplicate_rate, merge_blocking_miss_rate
from .models import Distribution, PerPRMetrics, PRResultInput, SummaryMetrics
from .precision import valid_precision
from .recall import raw_recall, weighted_recall
from .verdict import verdict_flags


def _resource_fields(result: PRResultInput) -> dict[str, int]:
    metadata = result.run_metadata
    if metadata is None:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_tokens": 0,
            "total_tokens": 0,
            "wall_time_ms": 0,
            "tool_calls": 0,
            "policy_violation_count": 0,
        }
    return {
        "input_tokens": metadata.input_tokens,
        "output_tokens": metadata.output_tokens,
        "cached_tokens": metadata.cached_tokens,
        "total_tokens": metadata.total_tokens,
        "wall_time_ms": metadata.wall_time_ms,
        "tool_calls": sum(stats.total for stats in metadata.tool_calls.values()),
        "policy_violation_count": len(metadata.policy_violations),
    }


def evaluate_pr(result: PRResultInput) -> PerPRMetrics:
    item = result.item
    rows = result.adjudications
    metadata = result.run_metadata
    contract_failure = bool(metadata and metadata.output_contract_failure)

    if item.invalidated:
        return PerPRMetrics(
            benchmark_id=item.benchmark_id,
            included=False,
            exclusion_reason=item.invalidation_reason or "BENCHMARK_INVALIDATED",
            output_contract_failure=contract_failure,
            **_resource_fields(result),
        )
    if item.clean_status == CleanStatus.AUTO_CERTIFIED_CLEAN and any(
        row.final_status == FinalStatus.VALID_NEW for row in rows
    ):
        return PerPRMetrics(
            benchmark_id=item.benchmark_id,
            included=False,
            exclusion_reason="BENCHMARK_INVALIDATED: VALID_NEW found on auto-certified clean PR",
            output_contract_failure=contract_failure,
            **_resource_fields(result),
        )

    review = result.review
    if review is not None:
        validate_adjudication_coverage((finding.id for finding in review.findings), rows)
    elif rows:
        raise ValueError("adjudications cannot exist without a parsed agent review")

    correct, false_approve, false_reject = verdict_flags(item, review)
    finding_count = len(review.findings) if review else 0
    per_raw = raw_recall(item, rows)
    per_weighted = weighted_recall(item, rows)
    if contract_failure and item.clean_status == CleanStatus.BUGGY:
        per_raw = 0.0
        per_weighted = 0.0
    if contract_failure:
        correct = False

    unverifiable = sum(row.final_status == FinalStatus.UNVERIFIABLE for row in rows)
    return PerPRMetrics(
        benchmark_id=item.benchmark_id,
        raw_recall=per_raw,
        weighted_recall=per_weighted,
        valid_precision=None if contract_failure else valid_precision(rows),
        verdict_correct=correct,
        false_approve=false_approve,
        false_reject=false_reject,
        merge_blocking_miss_rate=merge_blocking_miss_rate(item, rows),
        finding_count=finding_count,
        empty_review=item.clean_status == CleanStatus.BUGGY and finding_count == 0,
        duplicate_rate=duplicate_rate(rows),
        localization_accuracy=localization_accuracy(item, rows),
        severity_mae=severity_mae(rows),
        category_recall=category_recall(item, rows),
        blocker_inflation_rate=blocker_inflation_rate(rows),
        nit_rate=nit_rate(rows),
        adjudication_coverage=adjudication_coverage(rows),
        unverifiable_count=unverifiable,
        output_contract_failure=contract_failure,
        **_resource_fields(result),
    )


def _distribution(values: list[int]) -> Distribution | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(0.90 * len(ordered)))
    return Distribution(
        mean=statistics.fmean(ordered),
        median=statistics.median(ordered),
        p90=float(ordered[rank - 1]),
        maximum=float(ordered[-1]),
    )


def aggregate_results(
    results: list[PRResultInput],
    *,
    benchmark_version: str,
    rubric_version: str | None = None,
    judge_version: str | None = None,
    forced_invalidated_ids: set[str] | None = None,
) -> tuple[list[PerPRMetrics], SummaryMetrics]:
    per_pr = [evaluate_pr(result) for result in results]
    result_ids = {result.item.benchmark_id for result in results}
    globally_invalidated_ids = (set(forced_invalidated_ids or ()) & result_ids) | {
        result.item.benchmark_id
        for result in results
        if result.item.invalidated
        or (
            result.item.clean_status == CleanStatus.AUTO_CERTIFIED_CLEAN
            and any(row.final_status == FinalStatus.VALID_NEW for row in result.adjudications)
        )
    }
    if globally_invalidated_ids:
        per_pr = [
            metrics.model_copy(update={
                "included": False,
                "exclusion_reason": "BENCHMARK_INVALIDATED: invalid for all compared runs",
            })
            if result.item.benchmark_id in globally_invalidated_ids else metrics
            for result, metrics in zip(results, per_pr, strict=True)
        ]
    included_pairs = [
        (result, metrics)
        for result, metrics in zip(results, per_pr, strict=True)
        if metrics.included
    ]
    included_results = [pair[0] for pair in included_pairs]
    included_metrics = [pair[1] for pair in included_pairs]
    buggy_pairs = [pair for pair in included_pairs if pair[0].item.clean_status == CleanStatus.BUGGY]
    clean_pairs = [pair for pair in included_pairs if pair[0].item.clean_status == CleanStatus.AUTO_CERTIFIED_CLEAN]

    all_rows = [row for result in included_results for row in result.adjudications]
    matched_ids_by_benchmark = {
        id(result): covered_gt_ids(result.adjudications) for result in included_results
    }

    raw_macro_values = [metrics.raw_recall for _, metrics in buggy_pairs if metrics.raw_recall is not None]
    weighted_macro_values = [metrics.weighted_recall for _, metrics in buggy_pairs if metrics.weighted_recall is not None]
    total_gt = sum(len(result.item.gt_findings) for result, _ in buggy_pairs)
    matched_gt = sum(len(covered_gt_ids(result.adjudications)) for result, _ in buggy_pairs)
    total_weight = sum(SEVERITY_WEIGHT[f.severity] for result, _ in buggy_pairs for f in result.item.gt_findings)
    matched_weight = sum(
        SEVERITY_WEIGHT[f.severity]
        for result, _ in buggy_pairs
        for f in result.item.gt_findings
        if f.id in matched_ids_by_benchmark[id(result)]
    )

    request_change_pairs = [pair for pair in included_pairs if pair[0].item.expected_verdict == Verdict.REQUEST_CHANGES]
    approve_pairs = [pair for pair in included_pairs if pair[0].item.expected_verdict == Verdict.APPROVE]
    blocking_gt = [f for result in included_results for f in result.item.gt_findings if f.merge_blocking]
    blocking_misses = sum(
        f.id not in matched_ids_by_benchmark[id(result)]
        for result in included_results
        for f in result.item.gt_findings
        if f.merge_blocking
    )

    valid_statuses = {FinalStatus.MATCHED_GT, FinalStatus.VALID_PARTIAL, FinalStatus.VALID_NEW}
    precision_numerator = sum(row.final_status in valid_statuses for row in all_rows)
    precision_denominator = len(all_rows)
    duplicate_count = sum(row.final_status == FinalStatus.DUPLICATE for row in all_rows)
    unverifiable_count = sum(row.final_status == FinalStatus.UNVERIFIABLE for row in all_rows)

    localization_rows = []
    severity_rows = []
    category_totals: dict[str, int] = defaultdict(int)
    category_matches: dict[str, int] = defaultdict(int)
    for result in included_results:
        gt_by_id = {f.id: f for f in result.item.gt_findings}
        for finding in result.item.gt_findings:
            category_totals[finding.category.value] += 1
        for row in result.adjudications:
            if row.final_status == FinalStatus.MATCHED_GT and row.gt_id in gt_by_id:
                gt = gt_by_id[row.gt_id]
                category_matches[gt.category.value] += 1
                severity_rows.append(row)
                if gt.location_required:
                    localization_rows.append(row)

    category_values = {
        category: category_matches[category] / total
        for category, total in sorted(category_totals.items())
    }
    category_macro = statistics.fmean(category_values.values()) if category_values else None
    high_rows = [row for row in all_rows if row.predicted_severity in {Severity.CRITICAL, Severity.BLOCKER}]
    inflated = sum(
        row.final_status == FinalStatus.FALSE_POSITIVE
        or (
            row.effective_true_severity is not None
            and SEVERITY_VALUE[row.effective_true_severity] < SEVERITY_VALUE[Severity.BLOCKER]
        )
        for row in high_rows
    )
    nit_count = sum(
        row.final_status in valid_statuses and row.effective_true_severity == Severity.NIT
        for row in all_rows
    )
    round2_rows = sum(row.judge_round == 2 for row in all_rows)

    policy_violations = sum(metrics.policy_violation_count for metrics in included_metrics)
    coverage = 1.0 - unverifiable_count / len(all_rows) if all_rows else 1.0
    summary = SummaryMetrics(
        benchmark_version=benchmark_version,
        rubric_version=rubric_version,
        judge_version=judge_version,
        run_count=len(results),
        included_pr_count=len(included_results),
        buggy_pr_count=len(buggy_pairs),
        clean_pr_count=len(clean_pairs),
        raw_recall_macro=statistics.fmean(raw_macro_values) if raw_macro_values else None,
        raw_recall_micro=safe_div(matched_gt, total_gt),
        weighted_recall_macro=statistics.fmean(weighted_macro_values) if weighted_macro_values else None,
        weighted_recall_micro=safe_div(matched_weight, total_weight),
        valid_finding_precision=safe_div(precision_numerator, precision_denominator),
        verdict_accuracy=safe_div(sum(m.verdict_correct for m in included_metrics), len(included_metrics)),
        false_approve_rate=safe_div(sum(m.false_approve for _, m in request_change_pairs), len(request_change_pairs)),
        false_reject_rate=safe_div(sum(m.false_reject for _, m in approve_pairs), len(approve_pairs)),
        merge_blocking_miss_rate=safe_div(blocking_misses, len(blocking_gt)),
        findings_per_pr=_distribution([m.finding_count for m in included_metrics]),
        clean_pr_false_positive_rate=safe_div(
            sum(any(row.final_status == FinalStatus.FALSE_POSITIVE for row in result.adjudications) for result, _ in clean_pairs),
            len(clean_pairs),
        ),
        buggy_pr_empty_rate=safe_div(sum(m.empty_review for _, m in buggy_pairs), len(buggy_pairs)),
        duplicate_rate=safe_div(duplicate_count, len(all_rows)),
        policy_violation_count=policy_violations,
        policy_violation_run_rate=safe_div(sum(m.policy_violation_count > 0 for m in included_metrics), len(included_metrics)),
        input_tokens=sum(m.input_tokens for m in included_metrics),
        output_tokens=sum(m.output_tokens for m in included_metrics),
        cached_tokens=sum(m.cached_tokens for m in included_metrics),
        total_tokens=sum(m.total_tokens for m in included_metrics),
        wall_time_ms=sum(m.wall_time_ms for m in included_metrics),
        tool_calls=sum(m.tool_calls for m in included_metrics),
        localization_accuracy=safe_div(sum(row.location_correct is True for row in localization_rows), len(localization_rows)),
        severity_mae=(
            sum(abs(SEVERITY_VALUE[row.predicted_severity] - SEVERITY_VALUE[row.ground_truth_severity]) for row in severity_rows)
            / len(severity_rows)
            if severity_rows else None
        ),
        category_recall=category_values,
        category_macro_recall=category_macro,
        blocker_inflation_rate=safe_div(inflated, len(high_rows)),
        nit_rate=safe_div(nit_count, len(all_rows)),
        adjudication_coverage=coverage,
        provisional=coverage < 0.98,
        unverifiable_finding_count=unverifiable_count,
        benchmark_invalidated_pr_count=len(globally_invalidated_ids),
        judge_round2_rate=safe_div(round2_rows, len(all_rows)),
        output_contract_failure_count=sum(metrics.output_contract_failure for metrics in included_metrics),
    )
    return per_pr, summary
