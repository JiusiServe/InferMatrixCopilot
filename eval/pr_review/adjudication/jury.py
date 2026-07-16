"""Position-swapped multi-judge orchestration and consensus gates."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Protocol

from .models import JudgeVote


class JudgeBackend(Protocol):
    judge_id: str
    model_family: str

    def decide(self, *, task: str, payload: dict[str, Any], position: str) -> JudgeVote:
        ...


@dataclass(frozen=True)
class JuryResult:
    decision: str | None
    votes: list[JudgeVote]
    required_votes: int

    @property
    def reached_consensus(self) -> bool:
        return self.decision is not None

    @property
    def confidence(self) -> float:
        if not self.votes or self.decision is None:
            return 0.0
        supporting = [vote.confidence for vote in self.votes if vote.decision == self.decision]
        return sum(supporting) / len(supporting) if supporting else 0.0


def validate_judge_composition(backends: list[JudgeBackend], *, tested_model_family: str | None = None) -> None:
    if not backends:
        raise ValueError("jury needs at least one judge backend")
    ids = [backend.judge_id for backend in backends]
    if len(ids) != len(set(ids)):
        raise ValueError("judge IDs must be unique")
    if tested_model_family:
        controlled_votes = 2 * sum(backend.model_family == tested_model_family for backend in backends)
        total_votes = 2 * len(backends)
        if total_votes >= 6 and controlled_votes > 2:
            raise ValueError("tested model family may not control more than 2/6 standard votes")


def run_position_swapped_jury(
    backends: list[JudgeBackend],
    *,
    task: str,
    payload: dict[str, Any],
    required_votes: int | None = None,
    tested_model_family: str | None = None,
) -> JuryResult:
    validate_judge_composition(backends, tested_model_family=tested_model_family)
    votes: list[JudgeVote] = []
    for backend in backends:
        for position in ("A_TO_B", "B_TO_A"):
            vote = backend.decide(task=task, payload=payload, position=position)
            if vote.judge_id != backend.judge_id or vote.model_family != backend.model_family:
                raise ValueError("judge backend returned inconsistent identity")
            votes.append(vote)
    threshold = required_votes if required_votes is not None else (5 if len(votes) == 6 else len(votes))
    counts = Counter(vote.decision for vote in votes)
    decision, count = counts.most_common(1)[0]
    return JuryResult(decision if count >= threshold else None, votes, threshold)
