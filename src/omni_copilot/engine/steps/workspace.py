"""Workspace-facing steps: clean-tree guard and the cheap diff summary."""

from __future__ import annotations

import subprocess

from ...review.diff_summary import build_diff_summary
from ..step import FailureKind, StepContext, StepResult
from ._common import require_repo, step


@step("workspace.guard_clean", "deterministic", "read",
      "Refuse to start on a dirty working tree.")
async def _guard_clean(ctx: StepContext) -> StepResult:
    """Fail-closed pre-flight gate: refuse to start when the working tree is
    dirty, so a run never mixes its edits with pre-existing uncommitted changes.
    Runs `git status --porcelain`; a non-git or dirty tree returns BLOCKED (the
    dirty case carries a sample of the offending entries in `outputs`)."""
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    out = subprocess.run(["git", "status", "--porcelain"], cwd=str(repo),
                         capture_output=True, text=True, timeout=30)
    if out.returncode != 0:
        return StepResult(False, FailureKind.BLOCKED, f"not a git repo: {repo}")
    if out.stdout.strip():
        dirty = out.stdout.strip().splitlines()
        return StepResult(False, FailureKind.BLOCKED,
                          f"workspace dirty ({len(dirty)} entries) — refuse to start",
                          outputs={"dirty": dirty[:20]})
    return StepResult(True, summary="workspace clean")


@step("analysis.diff_summary", "deterministic", "read",
      "Cheap diffstat + out-of-scope/full-write flags.")
async def _diff_summary(ctx: StepContext) -> StepResult:
    """Cheap diffstat over the workspace against `params.base_ref` (default HEAD),
    flagging out-of-scope and full-file rewrites relative to `primary_files` in
    state. Delegates to `build_diff_summary`; returns the file/insertion/deletion
    counts as summary and the full summary dict in `outputs["diff_summary"]`."""
    repo = require_repo(ctx, must_exist=False)
    if isinstance(repo, StepResult):
        return repo
    summary = build_diff_summary(
        repo, base_ref=ctx.params.get("base_ref", "HEAD"),
        primary_files=tuple(ctx.state.get("primary_files", ())), trace=ctx.trace,
    )
    return StepResult(True, summary=f"{len(summary.changed_files)} files, "
                                    f"+{summary.insertions}/-{summary.deletions}",
                      outputs={"diff_summary": summary.__dict__})
