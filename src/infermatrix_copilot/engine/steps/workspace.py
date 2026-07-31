"""Workspace-facing steps: clean-tree guard and the cheap diff summary."""

from __future__ import annotations

import subprocess

from ...rebase_engine import worktree
from ...review.diff_summary import build_diff_summary
from ..step import FailureKind, StepContext, StepResult
from ._common import require_repo, step


def _porcelain(repo) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "status", "--porcelain"], cwd=str(repo),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=30)


@step("workspace.guard_clean", "deterministic", "read",
      "Refuse to start on a dirty working tree.")
async def _guard_clean(ctx: StepContext) -> StepResult:
    """Fail-closed pre-flight gate: refuse to start when the working tree is
    dirty, so a run never mixes its edits with pre-existing uncommitted changes.
    Runs `git status --porcelain`; a non-git or dirty tree returns BLOCKED (the
    dirty case carries a sample of the offending entries in `outputs`).
    Strictly read-only — the rebase pipeline's self-cleaning variant is the
    separate `workspace.guard_clean_rebase` (risk `write_workspace`)."""
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    out = _porcelain(repo)
    if out.returncode != 0:
        return StepResult(False, FailureKind.BLOCKED, f"not a git repo: {repo}")
    if out.stdout.strip():
        dirty = out.stdout.strip().splitlines()
        return StepResult(False, FailureKind.BLOCKED,
                          f"workspace dirty ({len(dirty)} entries) — refuse to start",
                          outputs={"dirty": dirty[:20]})
    return StepResult(True, summary="workspace clean")


@step("workspace.guard_clean_rebase", "deterministic", "write_workspace",
      "Clean-tree gate that first clears stale rebase-run residue.")
async def _guard_clean_rebase(ctx: StepContext) -> StepResult:
    """The rebase pipeline's variant of the clean-tree gate (port of
    `01_guard_branch_clean.sh`'s deterministic passes). It may MUTATE the
    workspace — hence its own step with risk `write_workspace`, keeping
    `workspace.guard_clean` honestly read-only for every other playbook:
    - `abort_stale_state: true` — abort a leftover merge/cherry-pick/revert/
      rebase from a halted prior run before judging cleanliness (its unmerged
      entries would otherwise read as ordinary dirt that `git restore` cannot
      clear).
    - `discard_untracked_patterns: [regex, ...]` — quick-discard untracked
      artifacts matching the adapter-supplied patterns (e.g. pytest-copied
      configs) before the dirty verdict; only untracked files are touched.
    Still fail-closed: anything left dirty after those passes is BLOCKED (the
    L2 discard/commit decision is a later agent step)."""
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    notes: list[str] = []
    if ctx.params.get("abort_stale_state"):
        aborted = worktree.abort_stale_inflight_state(repo)
        if aborted:
            notes.append(f"aborted stale in-flight state: {', '.join(aborted)}")

    out = _porcelain(repo)
    if out.returncode != 0:
        return StepResult(False, FailureKind.BLOCKED, f"not a git repo: {repo}")
    patterns = ctx.params.get("discard_untracked_patterns") or []
    if out.stdout.strip() and patterns:
        removed = worktree.discard_untracked_matching(repo, patterns)
        if removed:
            notes.append(f"discarded {len(removed)} untracked artifact(s)")
            out = _porcelain(repo)
    # `ignore_untracked_prefixes`: infrastructure files that must EXIST while
    # the run does (the shared checkout flock under locks/ — deleting a held
    # flock file would break mutual exclusion) are excluded from the dirty
    # VERDICT but never touched
    ignore = tuple(ctx.params.get("ignore_untracked_prefixes") or ())
    entries = [ln for ln in out.stdout.strip().splitlines()
               if not (ln.startswith("?? ")
                       and ln[3:].startswith(ignore))] \
        if ignore else out.stdout.strip().splitlines()
    if any(e.strip() for e in entries):
        dirty = entries
        return StepResult(False, FailureKind.BLOCKED,
                          f"workspace dirty ({len(dirty)} entries) — refuse to start",
                          outputs={"dirty": dirty[:20], "guard_notes": notes})
    summary = "workspace clean" + (f" ({'; '.join(notes)})" if notes else "")
    return StepResult(True, summary=summary,
                      outputs={"guard_notes": notes} if notes else {})


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
