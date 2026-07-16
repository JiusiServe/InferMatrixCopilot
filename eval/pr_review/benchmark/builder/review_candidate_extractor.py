"""Extract candidate GT records from historical inline review comments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .snapshot_selector import is_substantive_review_comment


@dataclass(frozen=True)
class ReviewCandidate:
    source_id: str
    body: str
    path: str
    start_line: int
    end_line: int
    created_at: str
    reviewer: str
    review_state: str | None
    diff_hunk: str
    original_commit_id: str | None


def extract_review_candidates(raw: dict[str, Any]) -> list[ReviewCandidate]:
    review_state_by_id = {review.get("id"): review.get("state") for review in raw.get("reviews", [])}
    result: list[ReviewCandidate] = []
    for comment in raw.get("review_comments", []):
        if not is_substantive_review_comment(comment):
            continue
        path = comment.get("path")
        line = comment.get("original_line") or comment.get("line")
        start_line = comment.get("original_start_line") or comment.get("start_line") or line
        if not path or not line or not start_line:
            continue
        result.append(ReviewCandidate(
            source_id=str(comment.get("id")),
            body=str(comment.get("body") or ""),
            path=str(path),
            start_line=int(start_line),
            end_line=int(line),
            created_at=str(comment.get("created_at") or ""),
            reviewer=str((comment.get("user") or {}).get("login") or "unknown"),
            review_state=review_state_by_id.get(comment.get("pull_request_review_id")),
            diff_hunk=str(comment.get("diff_hunk") or ""),
            original_commit_id=comment.get("original_commit_id"),
        ))
    return result
