"""Second-round cumulative gate for disputed adjudications."""

from __future__ import annotations

from collections import Counter

from .jury import JuryResult
from .models import JudgeVote


def combine_rounds(round1: JuryResult, round2_votes: list[JudgeVote], *, required_votes: int = 8) -> JuryResult:
    votes = [*round1.votes, *round2_votes]
    counts = Counter(vote.decision for vote in votes)
    decision, count = counts.most_common(1)[0]
    return JuryResult(decision if count >= required_votes else None, votes, required_votes)
