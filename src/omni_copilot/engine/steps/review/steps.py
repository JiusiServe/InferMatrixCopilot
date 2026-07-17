"""The two review step handlers: the conditional patch gate and the PR-review
agent step.

PR review is eval-informed (see eval/ANALYSIS.md): deterministic gate checks
catch the merge-state/CI issue class no diff-only model caught; evidence-
grounded tool use makes the strongest arm precise; a domain checklist fixes
topicality; a verify-and-rewrite pass fixes actionability. The prompt data is in
`prompts.py`; the deterministic sweep/render helpers in `utils.py`. The domain
checklist and the sweep language come from the repo profile (design §V2.2.2),
keeping the core prompt repo-neutral.
"""

from __future__ import annotations

import asyncio
import subprocess

from ....review.diff_summary import build_diff_summary
from ....review.planner import DEPTHS, plan_review
from ....review.reviewer import run_patch_review
from ....review.triggers import evaluate_triggers
from ...step import FailureKind, StepContext, StepResult
from .._common import gh_read_tools as _gh_read_tools
from .._common import repo_path as _repo_path
from .._common import step
from .prompts import _REVIEW_LENSES, _REVIEW_MERGE, _REVIEW_SYSTEM
from .utils import _SEVERITY_ORDER, _render_review_md, _sweep_targets


@step("review.patch_gate", "validation", "read",
      "Conditional patch review; fail-closed before pushes.")
async def _patch_gate(ctx: StepContext) -> StepResult:
    """Conditional Patch Review: cheap summary always; LLM review only on triggers."""
    repo = _repo_path(ctx)
    if repo is None:
        return StepResult(False, FailureKind.BLOCKED, "no repo path")
    summary = build_diff_summary(
        repo, base_ref=ctx.params.get("base_ref", "HEAD"),
        primary_files=tuple(ctx.state.get("primary_files", ())), trace=ctx.trace,
    )
    if not summary.changed_files and not summary.full_file_writes:
        return StepResult(True, summary="no diff to review",
                          outputs={"fired": [], "verdict": "not_required"})
    fired = evaluate_triggers(
        summary, ctx.settings,
        touched_modules=tuple(ctx.state.get("touched_modules", ())),
        pre_push=bool(ctx.params.get("pre_push", False)),
        knowledge_edit=bool(ctx.state.get("knowledge_edit", False)),
        high_risk_modules=ctx.state.get("high_risk_modules"),
    )
    ctx.trace.record("patch_review_triggers", fired=fired)
    if not fired:
        return StepResult(True, summary="no review triggers fired",
                          outputs={"fired": [], "verdict": "not_required"})
    diff = subprocess.run(["git", "diff", ctx.params.get("base_ref", "HEAD")],
                          cwd=str(repo), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60).stdout
    verdict = run_patch_review(ctx.llm, diff_text=diff, summary=summary,
                               fired_rules=fired, model=ctx.settings.reviewer)
    ctx.trace.record("patch_review", fired=fired, verdict=verdict.verdict,
                     critiques=verdict.critiques)
    if verdict.passing:
        return StepResult(True, summary=f"patch review lgtm (rules: {fired})",
                          outputs={"fired": fired, "verdict": "lgtm"})
    if verdict.verdict == "revise":
        return StepResult(False, FailureKind.REPLAN,
                          f"patch review requests revision: {verdict.critiques[:3]}",
                          outputs={"verdict": "revise", "critiques": verdict.critiques})
    return StepResult(False, FailureKind.ESCALATE,
                      f"patch review verdict={verdict.verdict}: {verdict.critiques[:3]}",
                      outputs={"verdict": verdict.verdict, "critiques": verdict.critiques})


def _risk_paths(adapter, settings) -> tuple[str, ...]:
    """High-risk path prefixes for the depth planner: the adapter's `risk:
    high` modules' local_paths when available, else the settings module-name
    fallback (matched as path segments, best effort)."""
    if adapter is not None and adapter.high_risk_modules:
        return tuple(p for m in adapter.high_risk_modules
                     for p in ((adapter.modules.get(m) or {})
                               .get("local_paths") or []))
    return tuple(settings.high_risk_modules)


@step("agent.review_diff", "agent", "read",
      "Evidence-grounded two-stage review: tool-loop investigation draft, "
      "then verify-and-rewrite editor pass.")
async def _review_diff(ctx: StepContext) -> StepResult:
    """PR review as a governed agent step (unified runtime): evidence pack,
    skill retrieval, enforced read-only tools, structured review_comments.
    Depth is adaptive (review/planner.py): deterministic rules route tiny
    low-risk diffs to one full-checklist pass and large/high-risk diffs to
    the full lens ensemble; only the gray middle spends one small planner
    call (robustness rationale for the ensemble: single runs have high
    variance; see eval/ANALYSIS.md)."""
    from ...agent_runtime import _resolve_adapter, run_agent_step, run_agent_step_ensemble

    diff = ctx.state.get("diff_text", "")
    if not diff:
        return StepResult(False, FailureKind.BLOCKED, "no diff_text in state")
    spec = ctx.state.get("task_spec") or {}

    # repo knowledge from the profile, not the core (design §V2.2.2): domain
    # checklist extension + the language key for the sweep extractors
    adapter = _resolve_adapter(ctx)
    language = "python"
    guidance = _REVIEW_SYSTEM
    if adapter is not None:
        language = str(adapter.manifest.get("repo", {}).get("language")
                       or "python")
        review_md = adapter.profile_dir / "review.md"
        try:
            if review_md.exists() and ctx.settings.profile_briefing_enabled:
                guidance += ("\n\n## Repo-specific review checklist "
                             "(from the repo profile)\n"
                             + review_md.read_text(encoding="utf-8")[:4_000])
        except OSError:
            pass

    common = dict(
        step_name="agent.review_diff",
        purpose=f"Review PR #{spec.get('pr')} like an engaged maintainer: "
                "grounded, specific, useful findings.",
        guidance=guidance,
        expected="review_comments with file/line/severity/comment/evidence; "
                 "APPROVE-equivalent = empty review_comments with a summary.",
        evidence={"pr_diff": str(diff),
                  "gate_report": ctx.state.get("gate_report", ""),
                  "sweep_targets": _sweep_targets(str(diff), language)},
        output_extension={"review_comments":
                          "list of {file, line, severity: blocker|major|minor|nit, "
                          "comment, evidence}"},
        extra_tools=_gh_read_tools(_repo_path(ctx)),
    )
    plan = None
    if not ctx.settings.review_ensemble:   # legacy kill-switch: single pass
        result, output = await run_agent_step(ctx, **common)
    else:
        override = str((spec.get("params") or {}).get("review_depth") or "") \
            .lower().strip()
        if override and override not in DEPTHS + ("auto",):
            # fail fast: a typo like "ful" must never silently downgrade an
            # explicitly requested full review
            return StepResult(False, FailureKind.BLOCKED,
                              f"invalid review_depth {override!r} — use "
                              "light|standard|full|auto")
        if not override or override == "auto":
            override = "" if ctx.settings.review_depth == "auto" \
                else ctx.settings.review_depth
        plan = await asyncio.to_thread(
            plan_review, str(diff), settings=ctx.settings,
            lens_names=tuple(l["name"] for l in _REVIEW_LENSES),
            lens_focus={l["name"]: l["focus"] for l in _REVIEW_LENSES},
            high_risk_paths=_risk_paths(adapter, ctx.settings),
            override=override, llm=ctx.llm,
            model=ctx.settings.review_planner_model
            or ctx.settings.model_for(spec.get("mode", "eco")))
        ctx.trace.record(
            "review_plan", depth=plan.depth, planner=plan.planner,
            reason=plan.reason, lenses=list(plan.lens_names),
            signals=plan.signals.as_dict() if plan.signals else None,
            input_tokens=plan.input_tokens, output_tokens=plan.output_tokens)
        if plan.depth == "light":
            result, output = await run_agent_step(
                ctx, max_iters=ctx.settings.review_light_max_iters, **common)
        else:
            lenses = [l for l in _REVIEW_LENSES
                      if l["name"] in plan.lens_names] or list(_REVIEW_LENSES)
            result, output = await run_agent_step_ensemble(
                ctx, lenses=lenses, merge_key="review_comments",
                merge_guidance=_REVIEW_MERGE, **common)
    # deterministic comment budget: severity-ordered, capped at 5 — the
    # low-signal tail goes first (reducers ignored a prompted cap; the cap is
    # a product budget, so it applies to every depth)
    comments = sorted(output.get("review_comments") or [],
                      key=lambda c: _SEVERITY_ORDER.get(
                          str(c.get("severity", "minor")).lower(), 2))
    output["review_comments"] = comments[:5]
    if not result.ok and output.get("review_comments"):
        # A review that FOUND defects is a successful review whose verdict is
        # REQUEST CHANGES — not a failed step. Agents conflate the PR's
        # mergeability with their own step status (observed live: four lenses
        # unanimously caught a removed-API survivor on the PR-time tree, set
        # needs_review, and the whole review was discarded). Same salvage
        # pattern as the issue-draft fix.
        result = StepResult(True,
                            summary=f"review salvaged from escalation — "
                                    f"{result.summary}",
                            outputs=result.outputs,
                            changed_files=result.changed_files)
    if plan is not None:
        result.outputs["review_plan"] = {"depth": plan.depth,
                                         "planner": plan.planner,
                                         "reason": plan.reason}
    if result.ok:
        review_md = _render_review_md(output)
        ctx.state["review_text"] = review_md
        result.outputs["review_text"] = review_md
        result.outputs.setdefault("state_updates", {})["review_text"] = review_md
        depth_note = f"; depth={plan.depth} via {plan.planner}" if plan else ""
        result.summary = (f"review produced ({len(output.get('review_comments') or [])} "
                          f"comments{depth_note}) — {result.summary}")
    return result
