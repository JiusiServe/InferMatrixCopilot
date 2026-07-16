"""Deterministic gate for Auto-certified Clean PR candidates."""

from __future__ import annotations

from dataclasses import dataclass

from ...adjudication.models import AdjudicationRow, FinalStatus
from ...benchmark.schema import Severity, Verdict
from ...runner.output_schema import AgentReview


@dataclass(frozen=True)
class CleanCertification:
    certified: bool
    reasons: tuple[str, ...]


def certify_clean_pr(
    reviewer_outputs: list[AgentReview],
    adjudications: list[list[AdjudicationRow]],
    *,
    certification_votes: int,
    required_votes: int = 5,
) -> CleanCertification:
    reasons: list[str] = []
    if len(reviewer_outputs) != 3 or len(adjudications) != 3:
        reasons.append("clean certification requires exactly three independent reviewer runs")
    for index, (review, rows) in enumerate(zip(reviewer_outputs, adjudications, strict=False), start=1):
        if review.verdict == Verdict.REQUEST_CHANGES:
            reasons.append(f"reviewer {index} returned REQUEST_CHANGES")
        if any(f.severity in {Severity.CRITICAL, Severity.BLOCKER} for f in review.findings):
            reasons.append(f"reviewer {index} reported a high-severity finding")
        non_fp = [row for row in rows if row.final_status != FinalStatus.FALSE_POSITIVE]
        if non_fp:
            reasons.append(f"reviewer {index} has non-FP adjudications: {[row.final_status.value for row in non_fp]}")
    if certification_votes < required_votes:
        reasons.append(f"clean certification jury only reached {certification_votes}/{required_votes} votes")
    return CleanCertification(not reasons, tuple(reasons))
