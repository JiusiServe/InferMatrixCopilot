import pytest

from eval.pr_review.metrics.models import SummaryMetrics
from eval.pr_review.reports.replicates import summarize_replicates
from eval.pr_review.spec import load_evaluation_spec


def summary(value):
    return SummaryMetrics(
        benchmark_version="v0.1",
        run_count=1,
        included_pr_count=1,
        buggy_pr_count=1,
        clean_pr_count=0,
        raw_recall_macro=value,
    )


def test_versioned_spec_matches_runtime_contracts():
    spec = load_evaluation_spec()
    assert spec.max_findings == 20
    assert spec.jury.first_round_required_votes == 5
    assert spec.adjudication_coverage_threshold == pytest.approx(0.98)


def test_replicates_report_mean_std_and_raw_runs():
    report = summarize_replicates([summary(0.5), summary(0.7), summary(0.9)])
    stats = report["metrics"]["raw_recall_macro"]
    assert stats["mean"] == pytest.approx(0.7)
    assert stats["standard_deviation"] == pytest.approx(0.2)
    assert stats["raw"] == [0.5, 0.7, 0.9]
