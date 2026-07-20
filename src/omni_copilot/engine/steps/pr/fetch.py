"""Read-only PR fetch steps: the PR diff and the deterministic gate report.

Both are injectable via state (`diff_text`, `gate_report`) so paths below the
network are offline-testable, and both degrade to BLOCKED (never crash) when
`gh` is unavailable.
"""

from __future__ import annotations

import json
import re
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


def _local_diff_fallback(repo: Path, pr: int) -> tuple[str, str]:
    """Reconstruct the PR diff locally when the gh/API diff endpoint refuses it
    (HTTP 406 on >20k-line diffs): resolve base+head from `gh pr view`, fetch
    both refs, and diff `merge-base(origin/<base>, head)..head` — the same
    three-dot semantics the API endpoint uses. Returns `(diff_text, detail)`;
    empty `diff_text` means the fallback also failed and `detail` says why."""
    code, out = _gh(["pr", "view", str(pr), "--json", "baseRefName,commits"],
                    cwd=repo)
    if code != 0:
        return "", f"pr view failed: {out[:200]}"
    try:
        data = json.loads(out or "{}")
    except json.JSONDecodeError:
        return "", "pr view returned non-JSON"
    base_ref = str(data.get("baseRefName") or "")
    commits = data.get("commits") or []
    head_sha = str(commits[-1].get("oid") or "") if commits else ""
    if not (base_ref and head_sha):
        return "", "base/head unresolvable from pr view"
    code, out = _git(repo, "fetch", "origin", base_ref, f"pull/{pr}/head",
                     timeout=300)
    if code != 0:
        return "", f"git fetch failed: {out[:200]}"
    code, out = _git(repo, "merge-base", f"origin/{base_ref}", head_sha)
    if code != 0:
        return "", f"merge-base failed: {out[:200]}"
    base_sha = out.strip()
    code, out = _git(repo, "diff", f"{base_sha}..{head_sha}", timeout=300)
    if code != 0:
        return "", f"git diff failed: {out[:200]}"
    return out, f"local git diff {base_sha[:12]}..{head_sha[:12]}"


_LINKED_ISSUE = re.compile(r"(?:fix(?:es|ed)?|close[sd]?|resolve[sd]?)\s*:?\s*#(\d+)",
                           re.IGNORECASE)


def _repo_full_name(ctx: StepContext, repo: str) -> str:
    """`owner/repo` of the checkout, resolved once via gh and cached in state —
    never taken from user/issue text (endpoint-injection guard)."""
    cached = ctx.state.get("_repo_full_name")
    if cached:
        return str(cached)
    code, out = _gh(["repo", "view", "--json", "nameWithOwner"], cwd=repo)
    full = ""
    if code == 0:
        try:
            full = str(json.loads(out or "{}").get("nameWithOwner") or "")
        except json.JSONDecodeError:
            full = ""
    ctx.state["_repo_full_name"] = full
    return full


def _last_n(items: list, n: int = 10) -> list:
    """Chronological last-n cap per source (B1's recall-vs-cost tradeoff)."""
    return list(items)[-n:]


def _clip(text: str, n: int = 700) -> str:
    text = str(text or "").strip()
    return text if len(text) <= n else text[:n] + " …[clipped]"


def _pr_context_bundle(ctx: StepContext, repo: str, pr: int) -> str:
    """Assemble the PR-side evidence bundle (design W1): title/body/labels
    always; discussion comments, review summaries, and inline review comments
    only in `pr_context_mode=full` (the eval-leakage policy: the frozen
    dataset's ground truth IS the human review discussion, so arm runs export
    PR_CONTEXT_MODE=no_discussion); linked issues (fixes/closes #N in body or
    branch name, capped 2) in both modes. Every sub-fetch failure degrades to
    a note — this bundle must never block the review."""
    mode = str(getattr(ctx.settings, "pr_context_mode", "full") or "full")
    parts: list[str] = []
    code, out = _gh(["pr", "view", str(pr), "--json",
                     "title,body,labels,headRefName,comments,reviews"], cwd=repo)
    data: dict = {}
    if code == 0:
        try:
            data = json.loads(out or "{}")
        except json.JSONDecodeError:
            data = {}
    else:
        parts.append("(pr view unavailable — partial context)")
    if data:
        labels = ", ".join(lb.get("name", "") for lb in data.get("labels") or [])
        parts.append(f"## PR description\n### {data.get('title', '')}"
                     + (f"  [labels: {labels}]" if labels else "")
                     + f"\n{_clip(data.get('body'), 4000)}")
    if mode == "full" and data:
        comments = [f"@{c.get('author', {}).get('login', '?')}: {_clip(c.get('body'))}"
                    for c in _last_n(data.get("comments") or [])]
        if comments:
            parts.append("## PR discussion (do not repeat these concerns — "
                         "build on or extend them)\n" + "\n".join(comments))
        reviews = [f"@{r.get('author', {}).get('login', '?')} "
                   f"[{r.get('state', '?')}]: {_clip(r.get('body'))}"
                   for r in _last_n(data.get("reviews") or []) if r.get("body")]
        if reviews:
            parts.append("## Review summaries\n" + "\n".join(reviews))
        full_name = _repo_full_name(ctx, repo)
        if full_name:  # inline review comments live on a separate endpoint
            code, out = _gh(["api", f"repos/{full_name}/pulls/{pr}/comments",
                             "--paginate", "-q",
                             ".[] | {user: .user.login, path, line, body}"],
                            cwd=repo)
            if code == 0 and out.strip():
                inline = []
                for line in _last_n(out.strip().splitlines()):
                    try:
                        c = json.loads(line)
                        inline.append(f"@{c.get('user', '?')} {c.get('path')}:"
                                      f"{c.get('line')}: {_clip(c.get('body'))}")
                    except json.JSONDecodeError:
                        continue
                if inline:
                    parts.append("## Inline review comments\n" + "\n".join(inline))
    # linked issues: acceptance criteria the diff must satisfy (both modes)
    hay = f"{(data.get('body') or '')} {(data.get('headRefName') or '')}"
    for num in list(dict.fromkeys(_LINKED_ISSUE.findall(hay)))[:2]:
        code, out = _gh(["issue", "view", num, "--json", "title,body"], cwd=repo)
        if code == 0:
            try:
                idata = json.loads(out or "{}")
                parts.append(f"## Linked issue #{num}: {idata.get('title', '')}\n"
                             + _clip(idata.get("body"), 2000))
            except json.JSONDecodeError:
                continue
    return "\n\n".join(p for p in parts if p)


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
    diff_note = ""
    if code != 0:
        # the API diff endpoint hard-fails on >20k-line diffs (HTTP 406
        # too_large) — reconstruct the diff from local git before giving up
        gh_err = out[:500]
        out, detail = _local_diff_fallback(Path(repo), int(pr))
        if not out:
            return StepResult(False, FailureKind.BLOCKED,
                              f"gh pr diff failed: {gh_err}; "
                              f"local fallback failed: {detail}")
        ctx.trace.record("diff_fallback", pr=int(pr), detail=detail,
                         gh_error=gh_err[:200])
        diff_note = f" via {detail}"
    ctx.state["diff_text"] = out
    # PR context bundle (design W1): description + discussion + linked issues —
    # the recall evidence a diff-only review structurally lacks. Degrades to a
    # partial bundle on any sub-fetch failure; never blocks the run.
    pr_context = _pr_context_bundle(ctx, repo, int(pr))
    ctx.state["pr_context"] = pr_context
    # pin the review tree to PR-time state (latent-gap mechanism); fall back
    # to the live checkout with a loud note when pinning is impossible
    wt_path, note = _pr_time_checkout(ctx, Path(repo), int(pr))
    ctx.state["repo_path"] = wt_path
    ctx.state["checkout_note"] = note
    return StepResult(
        True,
        summary=f"fetched PR #{pr} diff ({len(out)} chars{diff_note}, context "
                f"{len(pr_context)} chars); {note.split(' — ')[0]}",
        outputs={"state_updates": {"diff_text": out, "pr_context": pr_context,
                                   "repo_path": wt_path,
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
    # publish the PR state (OPEN|MERGED|CLOSED) — the renderer calibrates the
    # verdict wording on merged PRs (W2); previously MERGED was discarded
    # whenever no other gate fired
    ctx.state["pr_state"] = str(data.get("state") or "")
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
                               "state_updates": {
                                   "gate_report": report,
                                   "pr_state": ctx.state.get("pr_state", "")}})
