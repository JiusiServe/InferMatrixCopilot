"""Committed-range patch approval before a PR mutation is pushed.

This step owns only the pre-push review gate. The PR review agent in
``steps.py`` is a separate, read-only review workflow.
"""

from __future__ import annotations

import subprocess

from ....review.change_set import ChangeSet, ChangeSetError
from ....review.diff_summary import build_diff_summary
from ....review.reviewer import run_patch_review
from ....review.triggers import evaluate_triggers
from ...step import FailureKind, StepContext, StepResult
from .._common import repo_path as _repo_path
from .._common import step


@step("review.patch_gate", "validation", "read",
      "Conditional patch review; fail-closed before pushes.")
async def _patch_gate(ctx: StepContext) -> StepResult:
    """Conditional Patch Review: cheap summary always; LLM review only on triggers."""
    repo = _repo_path(ctx)
    if repo is None:
        return StepResult(False, FailureKind.BLOCKED, "no repo path")
    pre_push = bool(ctx.params.get("pre_push", False))
    change_set = None
    base_ref = str(ctx.params.get("base_ref") or "HEAD")
    if pre_push:
        base_ref = str(
            ctx.params.get("base_ref") or ctx.state.get("rebase_base_sha")
            or ctx.state.get("pr_initial_head_sha") or ""
        )
        try:
            change_set = ChangeSet.capture(repo, base_ref)
        except ChangeSetError as exc:
            return StepResult(False, FailureKind.BLOCKED, str(exc))
        if not change_set.diff_text:
            return StepResult(False, FailureKind.BLOCKED,
                              "no committed changes in the pre-push review range")
        base_ref = change_set.base_sha
    summary = build_diff_summary(
        repo, base_ref=base_ref,
        primary_files=tuple(ctx.state.get("primary_files", ())), trace=ctx.trace,
    )
    if not summary.changed_files and not summary.full_file_writes:
        if pre_push:
            return StepResult(False, FailureKind.BLOCKED,
                              "no committed changes in the pre-push review range")
        return StepResult(True, summary="no diff to review",
                          outputs={"fired": [], "verdict": "not_required"})
    fired = evaluate_triggers(
        summary, ctx.settings,
        touched_modules=tuple(ctx.state.get("touched_modules", ())),
        pre_push=pre_push,
        knowledge_edit=bool(ctx.state.get("knowledge_edit", False)),
        high_risk_modules=ctx.state.get("high_risk_modules"),
    )
    ctx.trace.record("patch_review_triggers", fired=fired)
    if not fired:
        return StepResult(True, summary="no review triggers fired",
                          outputs={"fired": [], "verdict": "not_required"})
    if change_set is not None:
        diff = change_set.diff_text
        if len(diff) > 60_000:
            return StepResult(False, FailureKind.ESCALATE,
                              "committed diff exceeds the patch reviewer's 60000-character budget")
    else:
        diff_result = subprocess.run(["git", "diff", base_ref],
                                     cwd=str(repo), capture_output=True, text=True,
                                     encoding="utf-8", errors="replace", timeout=60)
        if diff_result.returncode != 0:
            return StepResult(False, FailureKind.BLOCKED,
                              f"cannot read patch diff: {diff_result.stderr[:300]}")
        diff = diff_result.stdout
    verdict = run_patch_review(ctx.llm, diff_text=diff, summary=summary,
                               fired_rules=fired, model=ctx.settings.reviewer)
    ctx.trace.record("patch_review", fired=fired, verdict=verdict.verdict,
                     critiques=verdict.critiques)
    if verdict.passing:
        if change_set is not None:
            approval = {"base_sha": change_set.base_sha,
                        "head_sha": change_set.head_sha}
            ctx.state["approved_change_set"] = approval
            return StepResult(True, summary=f"patch review lgtm (rules: {fired})",
                              outputs={"fired": fired, "verdict": "lgtm",
                                       "state_updates": {"approved_change_set": approval}})
        return StepResult(True, summary=f"patch review lgtm (rules: {fired})",
                          outputs={"fired": fired, "verdict": "lgtm"})
    if verdict.verdict == "revise":
        return StepResult(False, FailureKind.REPLAN,
                          f"patch review requests revision: {verdict.critiques[:3]}",
                          outputs={"verdict": "revise", "critiques": verdict.critiques})
    return StepResult(False, FailureKind.ESCALATE,
                      f"patch review verdict={verdict.verdict}: {verdict.critiques[:3]}",
                      outputs={"verdict": verdict.verdict, "critiques": verdict.critiques})
