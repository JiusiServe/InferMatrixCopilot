"""PR-debug steps: collect failing checks (with real logs via the profile's CI
provider), bucket them by root-cause signature (hard cap escalates), and fix one
group's root cause as a governed agent step that commits the fix.

`ci_failures` is injectable via state for offline testing; a missing CI provider
is a recorded capability gap (debug degrades to name grouping), never a failure.
"""

from __future__ import annotations

import json
from pathlib import Path

from ....scopes import post_plan_scope
from ...step import FailureKind, StepContext, StepResult
from .._common import from_state, published, require_repo, step
from .._common import gh as _gh
from .._common import repo_path as _repo_path
from .._common import task_spec as _task_spec
from .utils import extract_signature


@step("pr.fetch_ci_failures", "deterministic", "read",
      "Collect failing checks for a PR (gh; injectable).")
async def _pr_fetch_ci_failures(ctx: StepContext) -> StepResult:
    """Collect a PR's failing checks via `gh pr checks`, enriching each with its
    real failure log. Returns injected `ci_failures` from state verbatim when
    present (offline testing). Reads the PR number from `task_spec`; a missing PR
    or a failed `gh` call degrades to BLOCKED rather than raising.

    Publishes two things to state (B2 `state_updates`): the full pre-fix
    `ci_check_snapshot` (every check, not just failures — the F2P/P2P metric needs
    the before-state to diff a post-push snapshot against), and `ci_failures`
    (the failing subset, each `{name, log, link}` with logs filled by
    `_enrich_ci_logs`)."""
    cached = from_state(ctx, "ci_failures")
    if cached is not None:
        return cached
    repo = _repo_path(ctx)
    spec = _task_spec(ctx)
    pr = spec.get("pr")
    if not pr:
        return StepResult(False, FailureKind.BLOCKED, "no PR number")
    code, out = _gh(["pr", "checks", str(pr), "--json", "name,state,link,bucket"], cwd=repo)
    if code != 0:
        return StepResult(False, FailureKind.BLOCKED, f"gh pr checks failed: {out[:400]}")
    checks = json.loads(out or "[]")
    # full pre-fix snapshot (not just failures): the F2P/P2P metric needs the
    # before-state to compare a post-push snapshot against (METRICS_RESEARCH §2)
    snapshot = {c.get("name", "?"): (c.get("bucket") or c.get("state", ""))
                for c in checks}
    ctx.state["ci_check_snapshot"] = snapshot
    ctx.trace.record("ci_check_snapshot", when="pre_fix", checks=snapshot)
    failing = [c for c in checks if c.get("bucket") == "fail"
               or c.get("state", "").upper() in ("FAILURE", "ERROR")]
    ctx.state["ci_failures"] = [
        {"name": c.get("name", "?"), "log": "", "link": c.get("link", "")} for c in failing
    ]
    enriched = _enrich_ci_logs(ctx, repo)
    return StepResult(True, summary=f"{len(failing)}/{len(checks)} checks failing"
                                    + (f", {enriched} log(s) fetched"
                                       if enriched else ""),
                      outputs={"failing": [c.get("name") for c in failing],
                               "state_updates": {
                                   "ci_failures": ctx.state["ci_failures"],
                                   "ci_check_snapshot": snapshot,
                               }})


def _enrich_ci_logs(ctx: StepContext, repo: Path | None) -> int:
    """Fetch real failure logs via the profile-selected CI provider.
    Best-effort: a missing provider is a recorded capability gap (pr-debug
    degrades to name grouping), never a failure."""
    failures = ctx.state.get("ci_failures") or []
    if not failures:
        return 0
    from ....ci.providers import provider_for
    from ...agent_runtime import _resolve_adapter

    provider, gap = provider_for(_resolve_adapter(ctx), ctx.settings,
                                 gh_runner=lambda args, cwd=None:
                                 _gh(args, cwd=cwd or repo))
    if provider is None:
        ctx.trace.record("capability_gap", capability="ci.provider",
                         step="pr.fetch_ci_failures", reason=gap,
                         effect="no CI logs; failures grouped by check name")
        return 0
    enriched = provider.enrich(failures)
    ctx.trace.record("ci_logs_enriched", provider=type(provider).__name__,
                     enriched=enriched, total=len(failures))
    return enriched


@step("pr.group_failures", "deterministic", "read",
      "Bucket failures by root-cause signature; hard cap escalates.")
async def _pr_group_failures(ctx: StepContext) -> StepResult:
    """Bucket the `ci_failures` from state into root-cause groups keyed by a
    normalized failure signature (extracted from each log, or the check name when
    no log), so the same failure across many jobs becomes one group to fix and the
    same failure across runs keys identically. Each group carries its member jobs
    and a single log excerpt.

    Publishes `failure_groups` to state (B2 `state_updates`). Fail-closed safety
    cap: more distinct groups than `settings.pr_debug_max_groups` returns ESCALATE
    (too tangled for the copilot — a human is needed) instead of proceeding."""
    from ....ci.normalize import normalize_signature

    failures = ctx.state.get("ci_failures", [])
    groups: dict[str, dict] = {}
    for f in failures:
        sig = extract_signature(f.get("log", "")) if f.get("log") else f.get("name", "unknown")
        sig = normalize_signature(sig)  # same failure ≠ new failure per run
        g = groups.setdefault(sig, {"signature": sig, "jobs": [], "log_excerpt": ""})
        g["jobs"].append(f.get("name", "?"))
        if f.get("log") and not g["log_excerpt"]:
            g["log_excerpt"] = f["log"][-4_000:]
    group_list = list(groups.values())
    max_groups = ctx.settings.pr_debug_max_groups
    if len(group_list) > max_groups:
        return StepResult(False, FailureKind.ESCALATE,
                          f"{len(group_list)} distinct failure groups exceeds the "
                          f"safety cap of {max_groups} — this PR needs a human",
                          outputs={"signatures": [g["signature"] for g in group_list]})
    ctx.state["failure_groups"] = group_list
    return published(f"{len(failures)} failures -> {len(group_list)} root-cause groups",
                     signatures=[g["signature"] for g in group_list],
                     state={"failure_groups": group_list})


_DEBUG_GUIDANCE = """You are debugging one grouped CI failure in a repo checkout.
Fix the ROOT CAUSE, not the symptom. Process: reproduce/inspect with read_file,
grep and run_shell; make the minimal correct edit; verify (run the relevant
test if possible, record it in tests_run); then run_shell
`git add -A && git commit -m "fix: <signature>"`.
status=success only after the fix is committed; otherwise status=failed with
failure_kind=escalate and an honest root_cause of what you found."""


@step("agent.debug_group", "agent", "write_workspace",
      "Fix one failure group's root cause; commits the fix.")
async def _pr_debug_group(ctx: StepContext) -> StepResult:
    """Fix one failure group's root cause as a governed agent step. The group is
    fanned out via `ctx.item` (signature + failing jobs + log excerpt); the agent
    runs in a post-plan scope over the repo checkout and must commit the fix
    (`_DEBUG_GUIDANCE`: root cause not symptom, verify, then `git commit`).

    Returns the agent's StepResult, rewriting its summary to carry the fix summary
    and verification on success, or the (typically ESCALATE) reason on failure.
    A missing repo checkout returns the require_repo BLOCKED result."""
    group = ctx.item or {}
    sig = group.get("signature", "unknown")
    repo = require_repo(ctx, must_exist=False)
    if isinstance(repo, StepResult):
        return repo
    from ...agent_runtime import run_agent_step

    result, output = await run_agent_step(
        ctx, step_name="agent.debug_group",
        purpose=f"Fix the root cause of the grouped CI failure: {sig}",
        guidance=_DEBUG_GUIDANCE,
        expected="root_cause + fix_summary + verification; fix committed",
        evidence={"failure_signature": sig,
                  "failing_jobs": str(group.get("jobs")),
                  "ci_log_excerpt": group.get("log_excerpt", "(no log)"),
                  "repo_note": f"Repo: {repo}; all shell commands with cwd={repo}."},
        output_extension={"root_cause": "the actual root cause found",
                          "fix_summary": "what was changed",
                          "verification": "how the fix was verified"},
        scope=post_plan_scope(repo),
        max_iters=ctx.settings.max_agent_iters,
    )
    if result.ok:
        result.summary = (f"'{sig}': {output.get('fix_summary', '')[:150]} "
                          f"(verified: {output.get('verification', '?')[:80]})")
    else:
        result.summary = f"'{sig}': {result.summary[:250]}"
    return result
