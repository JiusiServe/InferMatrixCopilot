import pytest

from eval.tasks.pr_review.adjudication.models import AdjudicationRow, FinalStatus
from eval.tasks.pr_review.benchmark.schema import BenchmarkItem
from eval.tasks.pr_review.metrics import PRResultInput, aggregate_results, evaluate_pr
from eval.tasks.pr_review.runner.output_schema import AgentReview
from eval.tasks.pr_review.runner.trace_collector import RunMetadata


def gt(gt_id, severity, blocking, category="correctness", line=1):
    return {
        "id": gt_id,
        "summary": f"summary {gt_id}",
        "description": f"description {gt_id}",
        "severity": severity,
        "category": category,
        "merge_blocking": blocking,
        "location_required": True,
        "accepted_locations": [{"file": "a.py", "start_line": line, "end_line": line}],
        "evidence": [{"file": "a.py", "start_line": line, "end_line": line}],
    }


def buggy_item(item_id="pr-1"):
    return BenchmarkItem.model_validate({
        "benchmark_id": item_id,
        "repository": "org/repo",
        "pr_number": 1,
        "base_sha": "a" * 40,
        "head_sha": "b" * 40,
        "title": "change",
        "changed_files": ["a.py"],
        "expected_verdict": "REQUEST_CHANGES",
        "clean_status": "buggy",
        "gt_findings": [
            gt("G1", "Blocker", True, line=1),
            gt("G2", "Minor", False, category="test", line=2),
        ],
    })


def clean_item(item_id="clean-1"):
    return BenchmarkItem.model_validate({
        "benchmark_id": item_id,
        "repository": "org/repo",
        "pr_number": 2,
        "base_sha": "c" * 40,
        "head_sha": "d" * 40,
        "title": "clean",
        "changed_files": ["a.py"],
        "expected_verdict": "APPROVE",
        "clean_status": "auto_certified_clean",
        "gt_findings": [],
    })


def finding(fid, severity="Blocker", verdict="REQUEST_CHANGES"):
    return {
        "id": fid,
        "title": fid,
        "description": "real issue under condition x",
        "severity": severity,
        "category": "correctness",
        "location": {"file": "a.py", "start_line": 1, "end_line": 1},
        "evidence": [{"file": "a.py", "start_line": 1, "end_line": 1, "reason": "code"}],
    }


def review(findings, verdict="REQUEST_CHANGES"):
    return AgentReview.model_validate({"verdict": verdict, "summary": "summary", "findings": findings})


def row(item_id, prediction, status, **kwargs):
    values = {
        "run_id": "r",
        "benchmark_id": item_id,
        "prediction_id": prediction,
        "final_status": status,
        "predicted_severity": kwargs.pop("predicted_severity", "Blocker"),
        "predicted_category": kwargs.pop("predicted_category", "correctness"),
    }
    values.update(kwargs)
    return AdjudicationRow.model_validate(values)


def metadata(item_id, **updates):
    values = {
        "run_id": f"r:{item_id}",
        "benchmark_version": "v0.1",
        "benchmark_id": item_id,
        "agent_version": "a",
        "model": "m",
        "prompt_version": "p",
        "tool_policy_version": "t",
        "repository_sha": "b" * 40,
        "started_at": "2026-01-01T00:00:00Z",
        "finished_at": "2026-01-01T00:00:01Z",
    }
    values.update(updates)
    return RunMetadata.model_validate(values)


def test_per_pr_metrics_follow_spec():
    item = buggy_item()
    rv = review([finding("P1"), finding("P2", severity="Minor")])
    rows = [
        row("pr-1", "P1", "MATCHED_GT", gt_id="G1", ground_truth_severity="Blocker",
            ground_truth_category="correctness", location_correct=True),
        row("pr-1", "P2", "FALSE_POSITIVE", predicted_severity="Minor"),
    ]
    metrics = evaluate_pr(PRResultInput(item=item, review=rv, adjudications=rows))
    assert metrics.raw_recall == pytest.approx(0.5)
    assert metrics.weighted_recall == pytest.approx(3 / 4)
    assert metrics.valid_precision == pytest.approx(0.5)
    assert metrics.merge_blocking_miss_rate == 0
    assert metrics.localization_accuracy == 1
    assert metrics.severity_mae == 0
    assert metrics.category_recall == {"correctness": 1.0, "test": 0.0}
    assert metrics.blocker_inflation_rate == 0


def test_partial_counts_for_precision_not_recall():
    item = buggy_item()
    rv = review([finding("P1", severity="Minor")])
    rows = [row("pr-1", "P1", "VALID_PARTIAL", gt_id="G2", jury_severity="Minor")]
    metrics = evaluate_pr(PRResultInput(item=item, review=rv, adjudications=rows))
    assert metrics.raw_recall == 0
    assert metrics.valid_precision == 1


def test_clean_valid_new_invalidates_for_all_metrics():
    item = clean_item()
    rv = review([finding("P1", severity="Minor")], verdict="APPROVE")
    rows = [row("clean-1", "P1", "VALID_NEW", predicted_severity="Minor", jury_severity="Minor")]
    metrics = evaluate_pr(PRResultInput(item=item, review=rv, adjudications=rows))
    assert metrics.included is False
    assert "BENCHMARK_INVALIDATED" in metrics.exclusion_reason


def test_output_contract_failure_sets_buggy_recall_zero_precision_na():
    item = buggy_item()
    metrics = evaluate_pr(PRResultInput(
        item=item,
        run_metadata=metadata("pr-1", output_contract_valid=False, output_contract_failure=True),
    ))
    assert metrics.raw_recall == 0
    assert metrics.weighted_recall == 0
    assert metrics.valid_precision is None
    assert metrics.verdict_correct is False


def test_aggregate_uses_macro_recall_and_micro_precision():
    item1 = buggy_item("pr-1")
    review1 = review([finding("P1")])
    rows1 = [row("pr-1", "P1", "MATCHED_GT", gt_id="G1", ground_truth_severity="Blocker",
                 ground_truth_category="correctness", location_correct=True)]

    item2 = clean_item("clean-1")
    review2 = review([finding("P2", severity="Minor")], verdict="REQUEST_CHANGES")
    rows2 = [row("clean-1", "P2", "FALSE_POSITIVE", predicted_severity="Minor")]

    per_pr, summary = aggregate_results([
        PRResultInput(item=item1, review=review1, adjudications=rows1),
        PRResultInput(item=item2, review=review2, adjudications=rows2),
    ], benchmark_version="v0.1")
    assert len(per_pr) == 2
    assert summary.raw_recall_macro == pytest.approx(0.5)
    assert summary.valid_finding_precision == pytest.approx(0.5)
    assert summary.verdict_accuracy == pytest.approx(0.5)
    assert summary.false_reject_rate == 1
    assert summary.clean_pr_false_positive_rate == 1
    assert summary.adjudication_coverage == 1
    assert summary.provisional is False


def test_unverifiable_below_98_percent_marks_provisional():
    item = clean_item()
    rv = review([finding("P1", severity="Minor")], verdict="APPROVE")
    rows = [row("clean-1", "P1", "UNVERIFIABLE", predicted_severity="Minor", unverifiable_reason="split")]
    _, summary = aggregate_results([PRResultInput(item=item, review=rv, adjudications=rows)], benchmark_version="v")
    assert summary.adjudication_coverage == 0
    assert summary.provisional is True

def test_clean_valid_new_invalidates_same_pr_for_all_compared_runs():
    clean = clean_item("clean-global")
    valid_review = review([finding("P1", severity="Minor")], verdict="APPROVE")
    valid_rows = [row("clean-global", "P1", "VALID_NEW", predicted_severity="Minor", jury_severity="Minor")]
    fp_review = review([finding("P2", severity="Minor")], verdict="APPROVE")
    fp_rows = [row("clean-global", "P2", "FALSE_POSITIVE", predicted_severity="Minor")]
    per_pr, summary = aggregate_results([
        PRResultInput(item=clean, review=valid_review, adjudications=valid_rows),
        PRResultInput(item=clean, review=fp_review, adjudications=fp_rows),
    ], benchmark_version="v")
    assert all(not metrics.included for metrics in per_pr)
    assert summary.included_pr_count == 0
    assert summary.benchmark_invalidated_pr_count == 1
