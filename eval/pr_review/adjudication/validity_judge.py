"""Reusable validity-jury entry points for new and partial findings."""

from __future__ import annotations

from typing import Any

from .jury import JudgeBackend, JuryResult, run_position_swapped_jury


def judge_finding_validity(
    backends: list[JudgeBackend],
    payload: dict[str, Any],
    *,
    required_votes: int = 5,
    tested_model_family: str | None = None,
) -> JuryResult:
    """Judge whether an unmatched prediction is VALID_NEW or FALSE_POSITIVE."""
    return run_position_swapped_jury(
        backends,
        task="finding_validity",
        payload=payload,
        required_votes=min(required_votes, 2 * len(backends)),
        tested_model_family=tested_model_family,
    )


def judge_partial_validity(
    backends: list[JudgeBackend],
    payload: dict[str, Any],
    *,
    required_votes: int = 5,
    tested_model_family: str | None = None,
) -> JuryResult:
    """Judge whether a non-matching but related prediction is VALID_PARTIAL."""
    return run_position_swapped_jury(
        backends,
        task="partial_validity",
        payload=payload,
        required_votes=min(required_votes, 2 * len(backends)),
        tested_model_family=tested_model_family,
    )
