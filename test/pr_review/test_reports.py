from eval.pr_review.metrics.models import SummaryMetrics
from eval.pr_review.reports import render_summary


def test_summary_contains_required_sections_and_no_composite():
    summary = SummaryMetrics(
        benchmark_version="v0.1",
        run_count=1,
        included_pr_count=1,
        buggy_pr_count=1,
        clean_pr_count=0,
    )
    text = render_summary(summary)
    assert "Core metrics" in text
    assert "Guardrails" in text
    assert "Diagnostics" in text
    assert "Evaluation validity" in text
    assert "No aggregate utility score" in text
