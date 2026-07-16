"""Convert a historical review candidate cluster into a frozen GT finding."""

from __future__ import annotations

from collections import Counter
from typing import Any

from ...adjudication.jury import JudgeBackend, run_position_swapped_jury
from ...benchmark.schema import Category, GroundTruthFinding, Severity
from .deduplicator import CandidateCluster


def _consensus_value(votes, field: str, *, decision: str, required_votes: int):
    values = [
        getattr(vote, field)
        for vote in votes
        if vote.decision == decision and getattr(vote, field) is not None
    ]
    if not values:
        return None
    value, count = Counter(values).most_common(1)[0]
    return value if count >= required_votes else None


def build_gt_from_cluster(
    cluster: CandidateCluster,
    *,
    evidence_bundle: dict[str, Any],
    judges: list[JudgeBackend],
    gt_id: str,
) -> GroundTruthFinding | None:
    payload = {
        "historical_comments": [candidate.__dict__ for candidate in cluster.candidates],
        "evidence_bundle": evidence_bundle,
        "questions": [
            "Does the issue really exist in the review-preceding snapshot?",
            "Is the core factual claim correct and non-stylistic?",
            "Did the subsequent change address it?",
            "Is it an independent GT finding?",
        ],
    }
    result = run_position_swapped_jury(
        judges,
        task="gt_validity",
        payload=payload,
        required_votes=min(5, 2 * len(judges)),
    )
    if result.decision != "VALID_GT":
        return None
    severity = _consensus_value(
        result.votes, "severity", decision="VALID_GT", required_votes=result.required_votes
    )
    category = _consensus_value(
        result.votes, "category", decision="VALID_GT", required_votes=result.required_votes
    )
    if not isinstance(severity, Severity) or not isinstance(category, Category):
        raise ValueError("GT jury votes must provide severity and category")
    primary = cluster.candidates[0]
    merge_blocking_values = [
        vote.merge_blocking
        for vote in result.votes
        if vote.decision == "VALID_GT" and vote.merge_blocking is not None
    ]
    merge_blocking = (
        severity in {Severity.CRITICAL, Severity.BLOCKER}
        or sum(bool(value) for value in merge_blocking_values) >= result.required_votes
    )
    if severity in {Severity.MINOR, Severity.NIT}:
        merge_blocking = False
    return GroundTruthFinding(
        id=gt_id,
        summary=primary.body.splitlines()[0][:200],
        description=primary.body,
        severity=severity,
        category=category,
        merge_blocking=merge_blocking,
        location_required=True,
        accepted_locations=[{
            "file": candidate.path,
            "start_line": candidate.start_line,
            "end_line": candidate.end_line,
        } for candidate in cluster.candidates],
        evidence=[{
            "file": primary.path,
            "start_line": primary.start_line,
            "end_line": primary.end_line,
            "reason": "historical maintainer review location",
        }],
    )
