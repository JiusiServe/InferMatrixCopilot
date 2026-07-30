"""Outward-writing PR steps: guarded pushes and structured GitHub reviews.

Both are choke points for the safety model. ``ci.push`` uses ``guard_push``;
``pr.post_review`` keeps the explicit-post plus ``ALLOW_POST`` gates, validates
finding locations against the fetched diff, and submits one GitHub review with
inline threads.
"""

from __future__ import annotations

import json
import re
import subprocess

from ....push import PushPolicy, guard_push
from ...step import FailureKind, StepContext, StepResult, StepSpec
from ..review.utils import _review_verdict
from .._common import gh as _gh
from .._common import register_step, step
from .._common import repo_path as _repo_path
from .._common import task_spec as _task_spec
from .fetch import _repo_full_name


@step("ci.push", "script", "push",
      "Guarded push (PushPolicy AND protected branches; dry-run default).")
async def _push(ctx: StepContext) -> StepResult:
    """The single C4 push choke point: authorize a git push through `guard_push`
    (PushPolicy AND protected branches) before ever running it. Rehydrates the
    `push_policy` from state (dict or PushPolicy) and the protected-branch list
    from state or settings.

    A denied decision returns FORBIDDEN. When authorized but `ALLOW_PUSH=0`
    (the default), it stays a dry run — reports the command it *would* run, never
    executes. Only with pushes enabled does it run the git command; a non-zero
    exit returns ESCALATE with the stderr tail."""
    repo = _repo_path(ctx)
    raw = ctx.state.get("push_policy")
    policy = raw if isinstance(raw, PushPolicy) else PushPolicy(**(raw or {}))
    protected = ctx.state.get("protected_branches") or ctx.settings.protected_branches
    ctx.trace.record("push_requested", remote=policy.remote, branch=policy.branch)
    decision = guard_push(policy, list(protected))
    if not decision.allowed:
        return StepResult(False, FailureKind.FORBIDDEN, decision.reason)
    if not ctx.settings.allow_push:
        return StepResult(True, summary=f"dry-run (ALLOW_PUSH=0): {' '.join(decision.command)}",
                          outputs={"dry_run": True, "command": list(decision.command)})
    out = subprocess.run(list(decision.command), cwd=str(repo), capture_output=True,
                         text=True, encoding="utf-8", errors="replace", timeout=300)
    if out.returncode != 0:
        return StepResult(False, FailureKind.ESCALATE,
                          f"push failed: {out.stderr[-1_000:]}")
    return StepResult(True, summary=f"pushed {policy.remote} HEAD:{policy.branch}")


_HUNK = re.compile(
    r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@"
)
_FULL_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _normalize_path(path: object) -> str:
    value = str(path or "").strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value[2:] if value.startswith("b/") else value


def _right_side_diff_lines(diff: str) -> dict[str, set[int]]:
    """Return RIGHT-side line numbers addressable by GitHub's review API."""
    lines: dict[str, set[int]] = {}
    path = ""
    new_line: int | None = None
    for raw in str(diff or "").splitlines():
        if raw.startswith("diff --git "):
            path, new_line = "", None
        elif new_line is None and raw.startswith("+++ "):
            candidate = raw[4:].strip()
            path = "" if candidate == "/dev/null" else _normalize_path(candidate)
            if path:
                lines.setdefault(path, set())
            new_line = None
        elif raw.startswith("@@"):
            match = _HUNK.match(raw)
            new_line = int(match.group(1)) if match and path else None
        elif path and new_line is not None:
            if raw.startswith("-") and not raw.startswith("---"):
                continue
            if raw.startswith("\\"):
                continue
            # Added and context lines both exist on the RIGHT side.
            lines[path].add(new_line)
            new_line += 1
    return lines


def _inline_comment(comment: dict) -> dict:
    severity = str(comment.get("severity") or "minor").lower()
    body = f"**[{severity}]** {str(comment.get('comment') or '').strip()}"
    evidence = str(comment.get("evidence") or "").strip()
    if evidence:
        body += f"\n\nEvidence: {evidence}"
    return {
        "path": _normalize_path(comment.get("file")),
        "line": int(comment["line"]),
        "side": "RIGHT",
        "body": body,
    }


def _partition_comments(
    comments: list[dict], diff: str,
) -> tuple[list[dict], list[dict]]:
    """Split findings into API-addressable comments and body fallbacks."""
    addressable = _right_side_diff_lines(diff)
    inline: list[dict] = []
    downgraded: list[dict] = []
    for raw in comments:
        comment = dict(raw) if isinstance(raw, dict) else {
            "comment": str(raw), "file": "", "line": None,
        }
        path = _normalize_path(comment.get("file"))
        try:
            line = int(comment.get("line"))
        except (TypeError, ValueError):
            line = 0
        if path and line > 0 and line in addressable.get(path, set()):
            comment["file"], comment["line"] = path, line
            inline.append(_inline_comment(comment))
        else:
            comment["file"], comment["line"] = path, line or "?"
            downgraded.append(comment)
    return inline, downgraded


def _fallback_section(comments: list[dict], reason: str = "") -> str:
    if not comments:
        return ""
    lines = [
        "### Findings without a valid current diff anchor",
        "",
        reason or (
            "These findings are preserved in the review body because their "
            "file/line could not be mapped to the fetched PR diff."
        ),
        "",
    ]
    for comment in comments:
        location = f"{comment.get('file') or '?'}:{comment.get('line') or '?'}"
        severity = str(comment.get("severity") or "minor").lower()
        text = str(comment.get("comment") or "").strip()
        evidence = str(comment.get("evidence") or "").strip()
        suffix = f" Evidence: {evidence}" if evidence else ""
        lines.append(f"- `{location}` [{severity}] — {text}{suffix}")
    return "\n".join(lines)


def _event_for_review(comments: list[dict], pr_state: str = "",
                      review_text: str = "") -> str:
    """Translate the product verdict to a submitted GitHub review event."""
    if comments:
        verdict = _review_verdict(comments, pr_state)
    else:
        match = re.search(
            r"\*\*Verdict:\*\*\s*(REQUEST CHANGES|COMMENT|APPROVE)",
            review_text or "", re.IGNORECASE)
        verdict = match.group(1).upper() if match else _review_verdict([], pr_state)
    event = {
        "REQUEST CHANGES": "REQUEST_CHANGES",
        "COMMENT": "COMMENT",
        "APPROVE": "APPROVE",
    }.get(verdict, "COMMENT")
    if str(pr_state).upper() != "OPEN" and event != "COMMENT":
        return "COMMENT"
    return event


def _review_payload(state: dict, *, current_head: str = "") -> tuple[dict, int]:
    """Build the API payload and return it with the downgrade count."""
    raw_comments = state.get("review_comments")
    comments = list(raw_comments) if isinstance(raw_comments, list) else []
    reviewed_head = str(state.get("pr_head_sha") or "").strip()
    stale_reason = ""
    if current_head and not reviewed_head and comments:
        stale_reason = (
            "These findings were reviewed without a recorded PR head SHA, so "
            "they were not attached to possibly newer code."
        )
    elif current_head and reviewed_head != current_head and comments:
        stale_reason = (
            f"The PR head changed after review "
            f"({reviewed_head[:12]} → {current_head[:12]}), so these findings "
            "were not attached to stale line anchors."
        )
    if stale_reason:
        inline, downgraded = [], [
            dict(comment) if isinstance(comment, dict)
            else {"comment": str(comment)}
            for comment in comments
        ]
    else:
        inline, downgraded = _partition_comments(
            comments, str(state.get("diff_text") or ""))
    review_text = str(state.get("review_text") or "")
    body = str(state.get("review_summary") or review_text or "Review complete.")
    fallback = _fallback_section(downgraded, stale_reason)
    if fallback:
        body = f"{body.rstrip()}\n\n{fallback}"
    payload = {
        "body": body,
        "event": _event_for_review(
            comments, str(state.get("pr_state") or ""), review_text),
        "comments": inline,
    }
    commit_id = current_head or reviewed_head
    if commit_id:
        payload["commit_id"] = commit_id
    return payload, len(downgraded)


def _current_pr_head(repo, pr: int) -> tuple[str, str]:
    """Resolve the current PR head SHA immediately before the write."""
    code, out = _gh(["pr", "view", str(int(pr)), "--json", "commits"], cwd=repo)
    if code != 0:
        return "", out[:400]
    try:
        commits = json.loads(out or "{}").get("commits") or []
    except (AttributeError, json.JSONDecodeError):
        commits = []
    sha = str(commits[-1].get("oid") or "") if commits else ""
    return sha, "" if sha else "PR head SHA missing from gh response"


async def _post_review(ctx: StepContext) -> StepResult:
    """Submit one GitHub review after both outward-write gates pass."""
    spec = _task_spec(ctx)
    if not (ctx.state.get("review_text") or ctx.state.get("review_comments")):
        return StepResult(False, FailureKind.BLOCKED, "no review output to post")
    if not spec.get("post"):
        return StepResult(True, summary="not posting GitHub review "
                          "(post flag not set)")

    payload, downgraded = _review_payload(ctx.state)
    inline_count = len(payload["comments"])
    if not ctx.settings.allow_post:
        return StepResult(
            True,
            summary=(
                "dry-run (ALLOW_POST=0): would post GitHub review "
                f"({inline_count} inline, {downgraded} downgraded, "
                f"event={payload['event']})"
            ),
            outputs={"dry_run": True, "payload": payload},
        )

    pr = spec.get("pr")
    if not pr:
        return StepResult(False, FailureKind.BLOCKED, "no PR number to post")
    repo = _repo_path(ctx)
    if repo is None:
        return StepResult(False, FailureKind.BLOCKED,
                          "repo checkout not configured")
    full_name = _repo_full_name(ctx, str(repo))
    if not _FULL_REPO.fullmatch(full_name):
        return StepResult(False, FailureKind.BLOCKED,
                          "could not resolve safe repository nameWithOwner")
    current_head, head_error = _current_pr_head(repo, int(pr))
    if not current_head:
        return StepResult(
            False, FailureKind.ESCALATE,
            f"could not verify current PR head before posting: {head_error}")
    payload, downgraded = _review_payload(
        ctx.state, current_head=current_head)
    inline_count = len(payload["comments"])

    ctx.run_dir.mkdir(parents=True, exist_ok=True)
    payload_path = ctx.run_dir / "github_review_payload.json"
    payload_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    code, out = _gh([
        "api", "--method", "POST",
        f"repos/{full_name}/pulls/{int(pr)}/reviews",
        "--input", str(payload_path),
    ], cwd=repo)
    if code != 0:
        return StepResult(
            False,
            FailureKind.ESCALATE,
            f"GitHub review posting failed: {out[:400]}",
            outputs={"artifacts": [str(payload_path)],
                     "inline": inline_count, "downgraded": downgraded,
                     "event": payload["event"]},
        )

    try:
        response = json.loads(out or "{}")
    except json.JSONDecodeError:
        response = {}
    url = str(response.get("html_url") or "")
    if not url:
        match = re.search(r"https://\S+", out or "")
        url = match.group(0) if match else ""
    ctx.trace.record(
        "posted_artifact", what="GitHub PR review", url=url, pr=int(pr),
        inline=inline_count, downgraded=downgraded, event=payload["event"])
    outputs = {
        "inline": inline_count,
        "downgraded": downgraded,
        "event": payload["event"],
        "payload_path": str(payload_path),
    }
    if url:
        outputs["url"] = url
    return StepResult(
        True,
        summary=(
            f"posted GitHub review ({inline_count} inline, "
            f"{downgraded} downgraded, event={payload['event']})"
        ),
        outputs=outputs,
    )


register_step(StepSpec(
    "pr.post_review", "script", "push", _post_review,
    "Post one GitHub review with validated inline comments "
    "(explicit post flag + ALLOW_POST)."))
