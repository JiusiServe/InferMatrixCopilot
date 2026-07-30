"""Outward-writing PR steps (risk=push): guarded pushes and GitHub reviews.

Both are the choke points the safety model governs — `ci.push` runs through
`guard_push` (PushPolicy AND protected branches, dry-run by default) and
`pr.post_review` requires explicit post intent plus `ALLOW_POST`.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from ....push import PushPolicy, guard_push
from ...step import FailureKind, StepContext, StepResult, StepSpec
from .._common import register_step, step
from .._common import gh as _gh
from .._common import post_step as _post_step
from .._common import repo_path as _repo_path
from .._common import task_spec as _task_spec
from ..review.utils import _render_review_md, _review_verdict


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


_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def _right_diff_lines(diff: str) -> dict[str, set[int]]:
    """Return new-side line numbers that GitHub can anchor with side=RIGHT."""
    lines: dict[str, set[int]] = {}
    path: str | None = None
    new_line: int | None = None
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            name = raw[4:]
            path = name[2:] if name.startswith("b/") else None
            new_line = None
            if path is not None:
                lines.setdefault(path.replace("\\", "/"), set())
            continue
        match = _HUNK.match(raw)
        if match:
            new_line = int(match.group(1))
            continue
        if path is None or new_line is None or raw.startswith("\\"):
            continue
        if raw.startswith("-") and not raw.startswith("---"):
            continue
        if raw.startswith(("+", " ")):
            lines[path].add(new_line)
            new_line += 1
    return lines


def _comment_body(comment: dict) -> str:
    severity = str(comment.get("severity") or "minor").lower()
    body = f"**[{severity}]** {str(comment.get('comment') or '').strip()}"
    if comment.get("evidence"):
        body += f"\n\nEvidence: {str(comment['evidence']).strip()}"
    return body


def _review_payload(comments: list[dict], diff: str, body: str,
                    pr_state: str = "") -> tuple[dict, list[dict]]:
    """Build the GitHub review payload and downgrade unanchorable findings."""
    anchors = _right_diff_lines(diff)
    inline: list[dict] = []
    fallback: list[dict] = []
    for comment in comments:
        path = str(comment.get("file") or "").replace("\\", "/").removeprefix("./")
        try:
            line = int(comment.get("line"))
        except (TypeError, ValueError):
            line = -1
        if path and line in anchors.get(path, set()):
            inline.append({"path": path, "line": line, "side": "RIGHT",
                           "body": _comment_body(comment)})
        else:
            fallback.append(comment)

    if fallback:
        downgraded = []
        for comment in fallback:
            path = str(comment.get("file") or "?")
            line = str(comment.get("line") or "?")
            downgraded.append(
                f"- `{path}:{line}` {_comment_body(comment).replace(chr(10), ' ')}")
        body = (body.rstrip() + "\n\n### Findings not posted inline\n"
                "These findings could not be anchored to a current changed line:\n"
                + "\n".join(downgraded))

    verdict = _review_verdict(comments, pr_state)
    event = {"REQUEST CHANGES": "REQUEST_CHANGES",
             "APPROVE": "APPROVE"}.get(verdict, "COMMENT")
    return {"body": body, "event": event, "comments": inline}, fallback


async def _post_review(ctx: StepContext) -> StepResult:
    """Post one GitHub review with inline findings, preserving both write gates."""
    spec = _task_spec(ctx)
    comments = ctx.state.get("review_comments")
    if comments is None:
        # Resume/backward-compatibility path for runs created before structured
        # comments were published into shared state.
        return await _post_step(
            "review_text",
            lambda task, body: ["pr", "comment", str(task.get("pr")),
                                "--body", body],
            "PR conversation comment")(ctx)
    if not isinstance(comments, list):
        return StepResult(False, FailureKind.BLOCKED,
                          "review_comments is not a list")
    if not spec.get("pr"):
        return StepResult(False, FailureKind.BLOCKED, "no PR number in task spec")
    if not spec.get("post"):
        return StepResult(True, summary="not posting GitHub review (post flag not set)")

    body = str(ctx.state.get("review_body") or "")
    if not body:
        body = _render_review_md(
            {"review_comments": comments, "summary": "No findings."},
            pr_state=str(ctx.state.get("pr_state") or ""),
            include_comment_details=False)
    payload, fallback = _review_payload(
        comments, str(ctx.state.get("diff_text") or ""), body,
        str(ctx.state.get("pr_state") or ""))
    if not ctx.settings.allow_post:
        return StepResult(
            True,
            summary=("dry-run (ALLOW_POST=0): would post GitHub review with "
                     f"{len(payload['comments'])} inline comment(s), "
                     f"{len(fallback)} fallback"),
            outputs={"dry_run": True, "payload": payload,
                     "inline_count": len(payload["comments"]),
                     "fallback_count": len(fallback)})

    repo = _repo_path(ctx)
    code, out = _gh(["repo", "view", "--json", "nameWithOwner"], cwd=repo)
    try:
        full_name = str(json.loads(out or "{}").get("nameWithOwner") or "")
    except json.JSONDecodeError:
        full_name = ""
    if code != 0 or not full_name:
        return StepResult(False, FailureKind.ESCALATE,
                          f"posting review failed: repository unresolved: {out[:300]}")

    endpoint = f"repos/{full_name}/pulls/{int(spec['pr'])}/reviews"
    code, out = _gh(["api", "--method", "POST", endpoint, "--input", "-"],
                    cwd=repo, input_text=json.dumps(payload, ensure_ascii=False))
    if code != 0:
        return StepResult(False, FailureKind.ESCALATE,
                          f"posting GitHub review failed: {out[:400]}")
    try:
        url = str(json.loads(out or "{}").get("html_url") or "")
    except json.JSONDecodeError:
        url = ""
    ctx.trace.record("posted_artifact", what="GitHub review", url=url,
                     pr=spec.get("pr"), inline_count=len(payload["comments"]),
                     fallback_count=len(fallback), event=payload["event"])
    summary = f"posted GitHub review with {len(payload['comments'])} inline comment(s)"
    if fallback:
        summary += f"; {len(fallback)} finding(s) downgraded to review body"
    outputs = {"inline_count": len(payload["comments"]),
               "fallback_count": len(fallback), "event": payload["event"]}
    if url:
        outputs["url"] = url
    return StepResult(True, summary=summary, outputs=outputs)


register_step(StepSpec(
    "pr.post_review", "script", "push", _post_review,
    "Post a structured GitHub review (explicit post flag + ALLOW_POST)."))
