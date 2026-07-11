"""Read-only PR fetch steps: the PR diff and the deterministic gate report.

Both are injectable via state (`diff_text`, `gate_report`) so paths below the
network are offline-testable, and both degrade to BLOCKED (never crash) when
`gh` is unavailable.
"""

from __future__ import annotations

import json
from pathlib import Path

from ...step import FailureKind, StepContext, StepResult
from .._common import from_state, require_repo, step
from .._common import gh as _gh
from .._common import git as _git
from .._common import repo_path as _repo_path


def _worktree_at(repo: Path, sha: str, dest: Path) -> tuple[bool, str]:
    """Materialize a detached worktree of `repo` at `sha` under `dest`,
    reusing an existing one already pinned to the same sha. Returns
    `(ok, detail)`; never raises — callers degrade to the live checkout."""
    try:
        if dest.exists():
            code, head = _git(dest, "rev-parse", "HEAD")
            if code == 0 and head.strip() == sha:
                return True, f"reused worktree @ {sha[:12]}"
            _git(repo, "worktree", "remove", "--force", str(dest))
        dest.parent.mkdir(parents=True, exist_ok=True)
        code, out = _git(repo, "worktree", "add", "--detach", str(dest), sha)
        if code != 0:
            return False, f"worktree add failed: {out[:300]}"
        return True, f"created worktree @ {sha[:12]}"
    except Exception as exc:  # noqa: BLE001 — never break the fetch step
        return False, f"worktree error: {exc}"


def _pr_time_checkout(ctx: StepContext, repo: Path, pr: int) -> tuple[str, str]:
    """Pin the review tree to the PR head (PR-TIME state): resolve headRefOid,
    fetch `pull/<n>/head` (works for open AND merged PRs), and create/reuse a
    detached worktree. Returns `(repo_path, checkout_note)` — the live checkout
    with a loud note when pinning is impossible, so reviews on post-merge main
    know a zero-survivor grep proves nothing about PR-time state.

    The latent-gap eval class (#4810 -> #4891) exists because reviewing on
    post-merge main hides exactly the sites the PR missed; a checklist rule
    could not fix what needed a mechanism."""
    injected = ctx.state.get("pr_head_sha")  # offline-test injection point
    sha = str(injected) if injected else ""
    if not sha:
        # `headRefOid` is not exposed by every gh version — the last commit's
        # oid is the PR head and is universally available
        code, out = _gh(["pr", "view", str(pr), "--json", "commits"], cwd=repo)
        if code == 0:
            commits = (json.loads(out or "{}").get("commits") or [])
            if commits:
                sha = str(commits[-1].get("oid") or "")
    if not sha:
        ctx.trace.record("capability_gap", capability="pr.head_sha",
                         step="pr.fetch_diff",
                         effect="reviewing post-merge main, not PR-time state")
        return str(repo), ("checkout: CURRENT MAIN (PR head unresolvable) — "
                           "the tree may already contain post-PR fixes; a "
                           "clean grep does NOT clear PR-time state")
    if not injected:
        code, out = _git(repo, "fetch", "origin", f"pull/{pr}/head")
        if code != 0:
            ctx.trace.record("capability_gap", capability="pr.head_fetch",
                             step="pr.fetch_diff", effect=out[:200])
            return str(repo), ("checkout: CURRENT MAIN (head fetch failed) — "
                               "post-PR fixes may be present; a clean grep "
                               "does NOT clear PR-time state")
    dest = Path.home() / ".omni-copilot" / "worktrees" / f"{repo.name}-pr{pr}"
    ok, detail = _worktree_at(repo, sha, dest)
    if not ok:
        ctx.trace.record("capability_gap", capability="pr.worktree",
                         step="pr.fetch_diff", effect=detail)
        return str(repo), ("checkout: CURRENT MAIN (worktree failed) — "
                           "post-PR fixes may be present; a clean grep does "
                           "NOT clear PR-time state")
    ctx.trace.record("pr_time_checkout", pr=pr, sha=sha, path=str(dest),
                     detail=detail)
    return str(dest), (f"checkout: PR-TIME TREE (head {sha[:12]}) — the tree "
                       "matches the diff exactly; repo-wide greps DO reflect "
                       "PR-time state")


@step("pr.fetch_diff", "deterministic", "read",
      "Fetch a PR diff via gh (read-only).")
async def _pr_fetch_diff(ctx: StepContext) -> StepResult:
    """Fetch a PR's unified diff via `gh pr diff` for the downstream reviewers.
    Reads the PR number from `task_spec`; returns injected `diff_text` from state
    verbatim when present (offline testing). A missing PR number or a failed `gh`
    call degrades to BLOCKED rather than raising.

    Publishes `diff_text` to state (B2 `state_updates`)."""
    cached = from_state(ctx, "diff_text")
    if cached is not None:
        return cached
    spec = ctx.state.get("task_spec") or {}
    pr = spec.get("pr") if isinstance(spec, dict) else None
    if not pr:
        return StepResult(False, FailureKind.BLOCKED, "no PR number in task spec")
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
    code, out = _gh(["pr", "diff", str(pr)], cwd=repo)
    if code != 0:
        return StepResult(False, FailureKind.BLOCKED, f"gh pr diff failed: {out[:500]}")
    ctx.state["diff_text"] = out
    # pin the review tree to PR-time state (latent-gap mechanism); fall back
    # to the live checkout with a loud note when pinning is impossible
    wt_path, note = _pr_time_checkout(ctx, Path(repo), int(pr))
    ctx.state["repo_path"] = wt_path
    ctx.state["checkout_note"] = note
    return StepResult(
        True,
        summary=f"fetched PR #{pr} diff ({len(out)} chars); {note.split(' — ')[0]}",
        outputs={"state_updates": {"diff_text": out, "repo_path": wt_path,
                                   "checkout_note": note}})


@step("pr.gate_check", "deterministic", "read",
      "Draft/merge-state/failing-checks gate report (deterministic).")
async def _pr_gate_check(ctx: StepContext) -> StepResult:
    """Deterministic gate check: draft/merge-state/failing checks — the issue
    class the eval showed no diff-only reviewer catches. Non-blocking: the
    findings go into the review context and the report."""
    cached = from_state(ctx, "gate_report")
    if cached is not None:
        return cached
    spec = ctx.state.get("task_spec") or {}
    pr = spec.get("pr") if isinstance(spec, dict) else None
    if not pr:
        return StepResult(False, FailureKind.BLOCKED, "no PR number in task spec")
    repo = _repo_path(ctx)
    lines: list[str] = []
    code, out = _gh(["pr", "view", str(pr), "--json",
                     "state,isDraft,mergeable,mergeStateStatus"], cwd=repo)
    if code != 0:
        ctx.state["gate_report"] = "gate check unavailable (gh failed)"
        return StepResult(True, summary="gate check unavailable (gh failed) — "
                                        "continuing without it",
                          outputs={"state_updates":
                                   {"gate_report": ctx.state["gate_report"]}})
    data = json.loads(out or "{}")
    if data.get("isDraft"):
        lines.append("PR is a DRAFT — review findings are provisional.")
    if data.get("mergeable") == "CONFLICTING" or \
            data.get("mergeStateStatus") in ("DIRTY", "BEHIND"):
        lines.append(f"MERGE STATE: {data.get('mergeStateStatus')} / "
                     f"{data.get('mergeable')} — the branch conflicts with or "
                     "trails the base; files may have moved/renamed on main. "
                     "Flag this as a blocking issue.")
    code, out = _gh(["pr", "checks", str(pr), "--json", "name,state,bucket"],
                    cwd=repo)
    if code == 0:
        failing = [c.get("name", "?") for c in json.loads(out or "[]")
                   if c.get("bucket") == "fail"
                   or c.get("state", "").upper() in ("FAILURE", "ERROR")]
        if failing:
            lines.append(f"FAILING CHECKS ({len(failing)}): {failing[:8]} — "
                         "do not re-argue what CI already reports; point at the gate.")
    report = "\n".join(lines) or "gates clean (mergeable, no failing checks)"
    ctx.state["gate_report"] = report
    return StepResult(True, summary=report.splitlines()[0][:120],
                      outputs={"gate_report": report,
                               "state_updates": {"gate_report": report}})
