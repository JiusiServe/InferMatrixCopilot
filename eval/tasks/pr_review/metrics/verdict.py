"""PR-level verdict metrics."""

from __future__ import annotations

from ..benchmark.schema import BenchmarkItem, Verdict
from ..runner.output_schema import AgentReview


def verdict_flags(item: BenchmarkItem, review: AgentReview | None) -> tuple[bool, bool, bool]:
    if review is None:
        return False, item.expected_verdict == Verdict.REQUEST_CHANGES, False
    correct = review.verdict == item.expected_verdict
    false_approve = item.expected_verdict == Verdict.REQUEST_CHANGES and review.verdict == Verdict.APPROVE
    false_reject = item.expected_verdict == Verdict.APPROVE and review.verdict == Verdict.REQUEST_CHANGES
    return correct, false_approve, false_reject
