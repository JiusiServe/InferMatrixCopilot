"""Select the last PR head snapshot before the first substantive review."""

from __future__ import annotations

from datetime import datetime
from typing import Any


_STYLE_MARKERS = {
    "nit", "typo", "format", "formatting", "style", "rename", "wording", "spelling",
}
_DEFECT_MARKERS = {
    "bug", "incorrect", "break", "failure", "race", "leak", "unsafe", "compatibility",
    "must", "wrong", "error", "crash", "deadlock", "regression", "request changes",
}


def parse_github_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def is_substantive_review_comment(comment: dict[str, Any]) -> bool:
    body = str(comment.get("body") or "").lower()
    if not body.strip():
        return False
    words = set(body.replace("_", " ").split())
    has_defect_signal = any(marker in body for marker in _DEFECT_MARKERS)
    style_only = bool(words & _STYLE_MARKERS) and not has_defect_signal
    return not style_only


def _substantive_review_points(raw: dict[str, Any]) -> list[tuple[datetime, str | None]]:
    points: list[tuple[datetime, str | None]] = []
    for review in raw.get("reviews", []):
        state = str(review.get("state", "")).upper()
        body = str(review.get("body") or "")
        if state == "CHANGES_REQUESTED" or (body and is_substantive_review_comment(review)):
            timestamp = review.get("submitted_at")
            if timestamp:
                points.append((parse_github_time(timestamp), review.get("commit_id")))
    for comment in raw.get("review_comments", []):
        if is_substantive_review_comment(comment) and comment.get("created_at"):
            points.append((
                parse_github_time(comment["created_at"]),
                comment.get("original_commit_id") or comment.get("commit_id"),
            ))
    return sorted(points, key=lambda value: value[0])


def first_substantive_review_time(raw: dict[str, Any]) -> datetime | None:
    points = _substantive_review_points(raw)
    return points[0][0] if points else None


def select_review_preceding_head(raw: dict[str, Any]) -> str:
    points = _substantive_review_points(raw)
    if not points:
        raise ValueError("PR has no substantive review timestamp")
    known_commits = {str(commit.get("sha")) for commit in raw.get("commits", []) if commit.get("sha")}
    review_time, reviewed_commit = points[0]
    # GitHub records the exact PR commit attached to a review/comment. Prefer it
    # over author dates, which may predate when a commit was pushed to the PR.
    if reviewed_commit and reviewed_commit in known_commits:
        return reviewed_commit

    eligible: list[tuple[datetime, str]] = []
    for commit in raw.get("commits", []):
        commit_meta = commit.get("commit", {})
        committer = commit_meta.get("committer", {})
        author = commit_meta.get("author", {})
        timestamp = committer.get("date") or author.get("date")
        sha = commit.get("sha")
        if timestamp and sha:
            committed_at = parse_github_time(timestamp)
            if committed_at < review_time:
                eligible.append((committed_at, sha))
    if not eligible:
        raise ValueError("no PR commit precedes the first substantive review")
    return max(eligible)[1]
