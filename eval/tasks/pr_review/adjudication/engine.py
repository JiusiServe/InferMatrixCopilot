"""End-to-end automatic finding adjudication using pluggable judge backends."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable

from ..benchmark.schema import BenchmarkItem, Severity
from ..runner.output_schema import AgentFinding, AgentReview
from .bipartite_matcher import MatchEdge, maximum_weight_matching
from .evidence import RepositoryEvidenceProvider
from .candidate_matcher import generate_candidates
from .jury import JudgeBackend, JuryResult, run_position_swapped_jury
from .jury_round2 import combine_rounds
from .models import AdjudicationRow, FinalStatus, JudgeVote


@dataclass(frozen=True)
class AdjudicationConfig:
    candidate_threshold: float = 0.20
    formal_match_threshold: float = 0.50
    first_round_votes: int = 5
    duplicate_votes: int = 4
    cumulative_round2_votes: int = 8
    tested_model_family: str | None = None


def _majority_optional(votes: list[JudgeVote], field: str, *, decision: str) -> Any | None:
    values = [getattr(vote, field) for vote in votes if vote.decision == decision and getattr(vote, field) is not None]
    if not values:
        return None
    return Counter(values).most_common(1)[0][0]


def _decision_with_round2(
    backends: list[JudgeBackend],
    *,
    task: str,
    payload: dict[str, Any],
    config: AdjudicationConfig,
    round2_backends: list[JudgeBackend] | None = None,
    first_round_required: int | None = None,
    round2_evidence_factory: Callable[[], dict[str, Any]] | None = None,
) -> tuple[JuryResult, int]:
    result = run_position_swapped_jury(
        backends,
        task=task,
        payload=payload,
        required_votes=min(first_round_required or config.first_round_votes, 2 * len(backends)),
        tested_model_family=config.tested_model_family,
    )
    if result.reached_consensus:
        return result, 1
    retry_backends = round2_backends or backends[:2]
    extra_votes: list[JudgeVote] = []
    enhanced = {**payload, "round1_disagreement": [vote.rationale for vote in result.votes]}
    if round2_evidence_factory is not None:
        enhanced["enhanced_evidence"] = round2_evidence_factory()
    for backend in retry_backends:
        for position in ("A_TO_B", "B_TO_A"):
            extra_votes.append(backend.decide(task=f"{task}_round2", payload=enhanced, position=position))
    return combine_rounds(
        result,
        extra_votes,
        required_votes=min(config.cumulative_round2_votes, len(result.votes) + len(extra_votes)),
    ), 2


def _finding_payload(prediction: AgentFinding, gt) -> dict[str, Any]:
    return {
        "prediction": prediction.model_dump(mode="json"),
        "ground_truth": gt.model_dump(mode="json"),
    }


def adjudicate_review(
    *,
    run_id: str,
    item: BenchmarkItem,
    review: AgentReview,
    judge_backends: list[JudgeBackend],
    round2_backends: list[JudgeBackend] | None = None,
    config: AdjudicationConfig | None = None,
    evidence_provider: RepositoryEvidenceProvider | None = None,
) -> list[AdjudicationRow]:
    """Classify every prediction and enforce one-to-one GT matching globally."""
    config = config or AdjudicationConfig()
    predictions = {finding.id: finding for finding in review.findings}
    gt_findings = {finding.id: finding for finding in item.gt_findings}
    candidates = generate_candidates(
        review.findings,
        item.gt_findings,
        threshold=config.candidate_threshold,
    )

    formal_edges: list[MatchEdge] = []
    edge_results: dict[tuple[str, str], tuple[JuryResult, int]] = {}
    partial_candidates: dict[str, tuple[str, JuryResult, int]] = {}
    for candidate in candidates:
        prediction = predictions[candidate.prediction_id]
        gt = gt_findings[candidate.gt_id]
        result, judge_round = _decision_with_round2(
            judge_backends,
            task="finding_match",
            payload={**_finding_payload(prediction, gt), "candidate_signals": candidate.signals},
            config=config,
            round2_backends=round2_backends,
            round2_evidence_factory=(
                (lambda prediction=prediction, gt=gt: evidence_provider.for_match(prediction, gt))
                if evidence_provider is not None else None
            ),
        )
        edge_results[(candidate.prediction_id, candidate.gt_id)] = (result, judge_round)
        if result.decision == "MATCH":
            weight = 0.6 * result.confidence + 0.4 * candidate.score
            if weight >= config.formal_match_threshold:
                formal_edges.append(MatchEdge(candidate.prediction_id, candidate.gt_id, weight))
        elif result.decision == "PARTIAL":
            previous = partial_candidates.get(candidate.prediction_id)
            if previous is None or result.confidence > previous[1].confidence:
                partial_candidates[candidate.prediction_id] = (candidate.gt_id, result, judge_round)

    matched = maximum_weight_matching(list(predictions), list(gt_findings), formal_edges, min_weight=config.formal_match_threshold)
    match_by_prediction = {edge.prediction_id: edge for edge in matched}
    matched_prediction_by_gt = {edge.gt_id: edge.prediction_id for edge in matched}
    rows: list[AdjudicationRow] = []

    for prediction_id, prediction in predictions.items():
        selected = match_by_prediction.get(prediction_id)
        if selected:
            result, judge_round = edge_results[(prediction_id, selected.gt_id)]
            gt = gt_findings[selected.gt_id]
            location = _majority_optional(result.votes, "location_correct", decision="MATCH")
            rows.append(AdjudicationRow(
                run_id=run_id,
                benchmark_id=item.benchmark_id,
                prediction_id=prediction_id,
                gt_id=gt.id,
                final_status=FinalStatus.MATCHED_GT,
                match_confidence=result.confidence,
                judge_round=judge_round,
                judge_votes=result.votes,
                predicted_severity=prediction.severity,
                ground_truth_severity=gt.severity,
                predicted_category=prediction.category,
                ground_truth_category=gt.category,
                location_correct=location,
            ))
            continue

        duplicate_target: str | None = None
        duplicate_result: JuryResult | None = None
        duplicate_round = 1
        for (pred_id, gt_id), (match_result, _) in edge_results.items():
            if pred_id != prediction_id or match_result.decision != "MATCH" or gt_id not in matched_prediction_by_gt:
                continue
            original_prediction_id = matched_prediction_by_gt[gt_id]
            original = predictions[original_prediction_id]
            duplicate_result, duplicate_round = _decision_with_round2(
                judge_backends,
                task="duplicate",
                payload={
                    "candidate": prediction.model_dump(mode="json"),
                    "accepted_prediction": original.model_dump(mode="json"),
                    "ground_truth": gt_findings[gt_id].model_dump(mode="json"),
                },
                config=config,
                round2_backends=round2_backends,
                first_round_required=config.duplicate_votes,
                round2_evidence_factory=(
                    (lambda prediction=prediction, original=original, gt_id=gt_id: evidence_provider.for_duplicate(
                        prediction, original, gt_findings[gt_id]
                    ))
                    if evidence_provider is not None else None
                ),
            )
            if duplicate_result.decision == "DUPLICATE":
                duplicate_target = original_prediction_id
                break
        if duplicate_target and duplicate_result:
            rows.append(AdjudicationRow(
                run_id=run_id,
                benchmark_id=item.benchmark_id,
                prediction_id=prediction_id,
                final_status=FinalStatus.DUPLICATE,
                match_confidence=duplicate_result.confidence,
                judge_round=duplicate_round,
                judge_votes=duplicate_result.votes,
                predicted_severity=prediction.severity,
                jury_severity=(
                    _majority_optional(duplicate_result.votes, "severity", decision="DUPLICATE")
                    or gt_findings[gt_id].severity
                ),
                predicted_category=prediction.category,
                duplicate_of=duplicate_target,
            ))
            continue

        partial = partial_candidates.get(prediction_id)
        if partial:
            gt_id, partial_result, partial_round = partial
            validity, validity_round = _decision_with_round2(
                judge_backends,
                task="partial_validity",
                payload=_finding_payload(prediction, gt_findings[gt_id]),
                config=config,
                round2_backends=round2_backends,
                round2_evidence_factory=(
                    (lambda prediction=prediction, gt_id=gt_id: evidence_provider.for_match(
                        prediction, gt_findings[gt_id]
                    ))
                    if evidence_provider is not None else None
                ),
            )
            if validity.decision == "VALID_PARTIAL":
                true_severity = _majority_optional(validity.votes, "severity", decision="VALID_PARTIAL") or gt_findings[gt_id].severity
                rows.append(AdjudicationRow(
                    run_id=run_id,
                    benchmark_id=item.benchmark_id,
                    prediction_id=prediction_id,
                    gt_id=gt_id,
                    final_status=FinalStatus.VALID_PARTIAL,
                    match_confidence=partial_result.confidence,
                    validity_confidence=validity.confidence,
                    judge_round=max(partial_round, validity_round),
                    judge_votes=[*partial_result.votes, *validity.votes],
                    predicted_severity=prediction.severity,
                    jury_severity=true_severity,
                    predicted_category=prediction.category,
                    ground_truth_category=gt_findings[gt_id].category,
                ))
                continue
            if validity.decision is None:
                rows.append(_unverifiable_row(run_id, item, prediction, validity, "partial validity jury did not converge"))
                continue

        validity, validity_round = _decision_with_round2(
            judge_backends,
            task="finding_validity",
            payload={"prediction": prediction.model_dump(mode="json")},
            config=config,
            round2_backends=round2_backends,
            round2_evidence_factory=(
                (lambda prediction=prediction: evidence_provider.for_validity(prediction))
                if evidence_provider is not None else None
            ),
        )
        if validity.decision == "VALID_NEW":
            severity = _majority_optional(validity.votes, "severity", decision="VALID_NEW") or prediction.severity
            rows.append(AdjudicationRow(
                run_id=run_id,
                benchmark_id=item.benchmark_id,
                prediction_id=prediction_id,
                final_status=FinalStatus.VALID_NEW,
                validity_confidence=validity.confidence,
                judge_round=validity_round,
                judge_votes=validity.votes,
                predicted_severity=prediction.severity,
                jury_severity=severity,
                predicted_category=prediction.category,
            ))
        elif validity.decision == "FALSE_POSITIVE":
            rows.append(AdjudicationRow(
                run_id=run_id,
                benchmark_id=item.benchmark_id,
                prediction_id=prediction_id,
                final_status=FinalStatus.FALSE_POSITIVE,
                validity_confidence=validity.confidence,
                judge_round=validity_round,
                judge_votes=validity.votes,
                predicted_severity=prediction.severity,
                predicted_category=prediction.category,
            ))
        else:
            rows.append(_unverifiable_row(run_id, item, prediction, validity, "validity jury did not converge"))
    return rows


def _unverifiable_row(
    run_id: str,
    item: BenchmarkItem,
    prediction: AgentFinding,
    result: JuryResult,
    reason: str,
) -> AdjudicationRow:
    return AdjudicationRow(
        run_id=run_id,
        benchmark_id=item.benchmark_id,
        prediction_id=prediction.id,
        final_status=FinalStatus.UNVERIFIABLE,
        judge_round=2,
        judge_votes=result.votes,
        predicted_severity=prediction.severity,
        predicted_category=prediction.category,
        unverifiable_reason=reason,
    )
