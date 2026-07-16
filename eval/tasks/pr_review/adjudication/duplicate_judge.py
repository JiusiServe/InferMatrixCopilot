"""Reusable duplicate-finding jury entry point."""

from __future__ import annotations

from typing import Any

from .jury import JudgeBackend, JuryResult, run_position_swapped_jury


def judge_duplicate(
    backends: list[JudgeBackend],
    payload: dict[str, Any],
    *,
    required_votes: int = 4,
    tested_model_family: str | None = None,
) -> JuryResult:
    """Judge whether two predictions express the same root cause."""
    return run_position_swapped_jury(
        backends,
        task="duplicate",
        payload=payload,
        required_votes=min(required_votes, 2 * len(backends)),
        tested_model_family=tested_model_family,
    )
