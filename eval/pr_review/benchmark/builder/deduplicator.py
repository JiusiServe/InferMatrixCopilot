"""Conservative candidate clustering; the GT jury still makes the final merge decision."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from .review_candidate_extractor import ReviewCandidate


@dataclass(frozen=True)
class CandidateCluster:
    candidates: tuple[ReviewCandidate, ...]


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", value.lower()))


def likely_same_root_cause(a: ReviewCandidate, b: ReviewCandidate, *, threshold: float = 0.72) -> bool:
    if a.path != b.path:
        return False
    line_distance = max(0, max(a.start_line, b.start_line) - min(a.end_line, b.end_line))
    if line_distance > 20:
        return False
    union = _tokens(a.body) | _tokens(b.body)
    jaccard = len(_tokens(a.body) & _tokens(b.body)) / len(union) if union else 0.0
    sequence = SequenceMatcher(None, a.body.lower(), b.body.lower()).ratio()
    return max(jaccard, sequence) >= threshold


def cluster_candidates(candidates: list[ReviewCandidate]) -> list[CandidateCluster]:
    clusters: list[list[ReviewCandidate]] = []
    for candidate in candidates:
        for cluster in clusters:
            if any(likely_same_root_cause(candidate, member) for member in cluster):
                cluster.append(candidate)
                break
        else:
            clusters.append([candidate])
    return [CandidateCluster(tuple(cluster)) for cluster in clusters]
