"""Deterministic candidate generation; it never decides a formal match."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from ..benchmark.schema import GroundTruthFinding
from ..runner.output_schema import AgentFinding


@dataclass(frozen=True)
class CandidateEdge:
    prediction_id: str
    gt_id: str
    score: float
    signals: dict[str, float]


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text.lower())}


def _interval_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    intersection = max(0, min(a_end, b_end) - max(a_start, b_start) + 1)
    union = max(a_end, b_end) - min(a_start, b_start) + 1
    return intersection / union if union else 0.0


def candidate_score(prediction: AgentFinding, gt: GroundTruthFinding) -> tuple[float, dict[str, float]]:
    locations = gt.accepted_locations
    same_file = max((1.0 if prediction.location.file == loc.file else 0.0 for loc in locations), default=0.0)
    line_overlap = max(
        (
            _interval_overlap(
                prediction.location.start_line,
                prediction.location.end_line,
                loc.start_line,
                loc.end_line,
            )
            if prediction.location.file == loc.file
            else 0.0
            for loc in locations
        ),
        default=0.0,
    )
    symbol = max(
        (
            1.0
            if prediction.location.symbol and loc.symbol and prediction.location.symbol == loc.symbol
            else 0.0
            for loc in locations
        ),
        default=0.0,
    )
    category = 1.0 if prediction.category == gt.category else 0.0
    pred_text = f"{prediction.title} {prediction.description}"
    gt_text = f"{gt.summary} {gt.description}"
    token_union = _tokens(pred_text) | _tokens(gt_text)
    token_similarity = len(_tokens(pred_text) & _tokens(gt_text)) / len(token_union) if token_union else 0.0
    sequence = SequenceMatcher(None, pred_text.lower(), gt_text.lower()).ratio()
    semantic_proxy = max(token_similarity, sequence)
    signals = {
        "same_file": same_file,
        "line_overlap": line_overlap,
        "symbol": symbol,
        "category": category,
        "description": semantic_proxy,
    }
    score = (
        0.25 * same_file
        + 0.20 * line_overlap
        + 0.20 * symbol
        + 0.10 * category
        + 0.25 * semantic_proxy
    )
    return score, signals


def generate_candidates(
    predictions: list[AgentFinding],
    gt_findings: list[GroundTruthFinding],
    *,
    threshold: float = 0.20,
    max_per_prediction: int = 5,
) -> list[CandidateEdge]:
    edges: list[CandidateEdge] = []
    for prediction in predictions:
        ranked: list[CandidateEdge] = []
        for gt in gt_findings:
            score, signals = candidate_score(prediction, gt)
            if score >= threshold:
                ranked.append(CandidateEdge(prediction.id, gt.id, score, signals))
        edges.extend(sorted(ranked, key=lambda edge: edge.score, reverse=True)[:max_per_prediction])
    return edges
