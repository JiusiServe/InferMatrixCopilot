"""Read-only PR fetch steps: the PR diff and the deterministic gate report.

Both are injectable via state (`diff_text`, `gate_report`) so paths below the
network are offline-testable, and both degrade to BLOCKED (never crash) when
`gh` is unavailable.
"""

from __future__ import annotations

import json

from ...step import FailureKind, StepContext, StepResult
from .._common import from_state, require_repo, step
from .._common import gh as _gh
from .._common import repo_path as _repo_path


@step("pr.fetch_diff", "deterministic", "read",
      "Fetch a PR diff via gh (read-only).")
async def _pr_fetch_diff(ctx: StepContext) -> StepResult:
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
    return StepResult(True, summary=f"fetched PR #{pr} diff ({len(out)} chars)",
                      outputs={"state_updates": {"diff_text": out}})


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
