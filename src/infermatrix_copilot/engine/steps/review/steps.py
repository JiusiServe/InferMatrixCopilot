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
import json
import subprocess
from dataclasses import replace
from pathlib import Path

from ....llm import parse_json_reply

from ....review.diff_summary import build_diff_summary
from ....review.planner import DEFAULT_STANDARD_LENSES, DEPTHS, plan_review
from ....review.reviewer import run_patch_review
from ....review.triggers import evaluate_triggers
from ...step import FailureKind, StepContext, StepResult
from .._common import gh_read_tools as _gh_read_tools
from .._common import repo_path as _repo_path
from .._common import step
from .anchor import resolve_review_comments
from .prompts import (
    _REVIEW_DEEP_PASSES,
    _REVIEW_LENSES,
    _REVIEW_LIGHT_PROTOCOL,
    _REVIEW_MERGE,
    _REVIEW_SYSTEM,
)
from .utils import (
    _SEVERITY_ORDER,
    _render_review_md,
    _render_review_summary,
    _sweep_targets,
)


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


def _consumer_sweep(repo: str | None, diff: str) -> str:
    """Deterministic consumer listing: for each symbol whose definition the
    diff touches, every in-repo reference (`git grep -nw`), capped. The
    highest-variance recall failure was consumers of changed behavior living
    in files (or file regions) no lens ever paged to; listing the exact
    locations makes that coverage mechanical instead of stochastic. Runs
    against the PR-time worktree, so hits reflect the reviewed tree."""
    if not repo:
        return ""
    from .utils import _changed_symbols

    out: list[str] = []
    for sym in _changed_symbols(diff)[:8]:
        try:
            r = subprocess.run(["git", "grep", "-n", "-w", sym],
                               cwd=repo, capture_output=True, text=True,
                               timeout=20)
        except (OSError, subprocess.SubprocessError):
            continue
        hits = [h for h in (r.stdout or "").splitlines()
                if not h.split(":", 1)[0].endswith((".md", ".rst"))][:10]
        if hits:
            out.append(f"`{sym}` referenced at:")
            out += [f"- {h[:160]}" for h in hits]
    if not out:
        return ""
    return ("IN-REPO REFERENCES OF CHANGED SYMBOLS — for each, check the "
            "caller still holds under the NEW behavior (page to it if the "
            "file is large); a consumer in a file the diff does not touch "
            "is where breakage hides:\n" + "\n".join(out))


async def _promote_uncovered(ctx: StepContext, output: dict,
                             spec: dict) -> dict:
    """Coverage-promotion pass: one tool-less LLM call that promotes
    maintainer-relevant concerns ALREADY PRESENT in the run's own findings/
    validated/blockers lines into review comments.

    Train forensics showed the recall loss is often not investigation but
    conversion: the ground-truth concern sat verbatim in a lens's findings or
    the run's blockers ("the VoxCPM2 regression is a separate mechanism",
    "NPU lane is red", "diff evidence was truncated") and never became a
    comment. Promotion is grounded by construction — the call may only cite
    material from the lines it is shown, never new claims — so it raises
    recall without the speculation cost of widening the lens budget."""
    findings = [str(x) for x in (output.get("findings") or [])][:60]
    blockers = [str(x) for x in (output.get("blockers") or [])][:10]
    assumptions = [str(x) for x in (output.get("assumptions") or [])][:10]
    comments = output.get("review_comments") or []
    if not (findings or blockers) or ctx.llm is None \
            or not getattr(ctx.llm, "available", False):
        ctx.trace.record("review_coverage_skipped",
                         step="agent.review_diff",
                         reason="no findings" if not (findings or blockers)
                         else "no llm")
        return output
    system = (
        "You are the coverage editor for a PR review. You receive the "
        "review's KEPT COMMENTS plus the reviewers' raw FINDINGS/BLOCKERS/"
        "ASSUMPTIONS lines. Identify up to 3 maintainer-relevant concerns "
        "that appear in the raw lines but are NOT covered by any kept "
        "comment, and promote each into a comment object. Prioritize these "
        "classes: blast-radius of a changed default/shared value, benchmark "
        "evidence for perf/capacity changes, test integrity (a test that "
        "cannot fail or is never selected), dependency-version "
        "compatibility, resource lifecycle on abort paths, scope explicitly "
        "left unfixed (linked-issue remainder), red CI on the head. Rules: "
        "(1) ONLY promote what the raw lines already state — no new claims, "
        "no re-investigation; quote the source line in `evidence`. (2) A "
        "promoted validation line becomes a question or scoping ask, not an "
        "invented defect. (3) severity: minor unless the raw line "
        "demonstrates breakage (then major). (4) If everything relevant is "
        "already covered, return no additions. Reply with exactly one JSON "
        'object: {"additions": [{"file": str, "line": int, "severity": '
        '"major"|"minor", "comment": str, "evidence": str}]}')
    prompt = (
        "## KEPT COMMENTS\n"
        + json.dumps([{k: c.get(k) for k in ("file", "line", "severity",
                                             "comment")}
                      for c in comments], ensure_ascii=False, indent=1)
        + "\n\n## RAW FINDINGS\n" + "\n".join(f"- {x}" for x in findings)
        + ("\n\n## BLOCKERS\n" + "\n".join(f"- {x}" for x in blockers)
           if blockers else "")
        + ("\n\n## ASSUMPTIONS\n" + "\n".join(f"- {x}" for x in assumptions)
           if assumptions else ""))
    try:
        _tt = ctx.settings.tier_target(spec.get("mode", "eco"))
        llm = (ctx.llm.for_target(_tt)
               if hasattr(ctx.llm, "for_target") else ctx.llm)
        reply = await asyncio.to_thread(
            llm.create, system=system,
            messages=[{"role": "user", "content": prompt}],
            model=_tt.model, role="reducer",
            max_tokens=max(4096, ctx.settings.llm_max_tokens))
        obj = parse_json_reply(reply.text or "")
    except Exception as exc:  # never fail the review over the extra pass —
        ctx.trace.record("review_coverage_skipped",   # but say WHY, loudly
                         step="agent.review_diff",
                         reason=f"{type(exc).__name__}: {exc}"[:200])
        return output
    additions = (obj or {}).get("additions") if isinstance(obj, dict) else None
    kept: list[dict] = []
    for a in (additions or [])[:3]:
        if not isinstance(a, dict) or not a.get("comment") \
                or not a.get("evidence"):
            continue
        kept.append({"file": str(a.get("file") or "?"),
                     "line": a.get("line"),
                     "severity": str(a.get("severity") or "minor").lower(),
                     "comment": str(a["comment"]),
                     "evidence": str(a["evidence"]),
                     # ordering tag: promoted items carry a protected-class
                     # concern; under the comment budget they rank ahead of
                     # uncorroborated same-severity items (stripped at cap)
                     "corroborated_by": ["coverage"]})
    if kept:
        output = dict(output)
        output["review_comments"] = list(comments) + kept
        ctx.trace.record("review_coverage_promoted",
                         step="agent.review_diff", added=len(kept))
    else:
        ctx.trace.record("review_coverage_skipped",
                         step="agent.review_diff",
                         reason="model returned no valid additions",
                         parsed=obj is not None,
                         reply_head=str(reply.text or "")[:200])
    return output


_VERIFY_GUIDANCE = """You verify ONE draft review comment against the PR-time tree.

In order, with the minimum tool calls (your budget is small):
1. Anchor: does the cited file:line (or quoted snippet) exist as the comment
   claims? Read that region of the file.
2. Claim: is the asserted problem true of the code you just read? If the
   comment asserts consumers/callers/tests elsewhere, grep for them and read
   the one that decides the claim.
3. Severity: major requires a real defect in the changed code or a required
   update the diff lacks; "consider adding X" polish is minor at most.

Verdicts:
- confirmed: you READ the code that makes the claim true. You MUST return
  `evidence` as SELF-CONTAINED PROOF a reader with no repo access can check:
  the decisive code line(s) QUOTED VERBATIM with their file:line, e.g.
  'serving_speech.py:3711 `extra_args["tts_local_seed"] = seed` — set for
  every model, no qwen3_tts gate'. A narrative like "read the file, claim
  holds" is NOT proof and scores as speculation downstream. Optionally
  return a tightened `comment` (sharper wording, exact file/line) — keep
  the substance, never soften a confirmed defect.
- refuted: the code CONTRADICTS the claim (misread, already handled, wrong
  file). Refuted is an evidence conclusion, never a budget one.
- unverifiable: you could not decide within budget.

Confirming from plausibility alone is the one failure this pass exists to
prevent — when in doubt between confirmed and unverifiable, unverifiable."""


async def _verify_comments(ctx: StepContext, output: dict,
                           common: dict) -> dict:
    """Per-comment agentic verification (val-gate lesson: with recall at
    parity the arm lost on per-comment grounding). Each draft comment gets
    one small tool-loop that must anchor and re-derive the claim on the
    PR-time tree: refuted comments drop, unverifiable ones demote one
    severity step, confirmed ones may be tightened in wording/position. A
    verification-step failure keeps the comment unchanged — this pass may
    only improve precision, never silently delete recall."""
    from ...agent_runtime import run_agent_step

    comments = list(output.get("review_comments") or [])
    if not comments or not ctx.settings.review_verify_comments:
        return output
    sem = asyncio.Semaphore(ctx.settings.review_verify_concurrency)
    diff_ev = str((common.get("evidence") or {}).get("pr_diff") or "")

    async def _one(i: int, c: dict):
        async with sem:
            # pr_diff leads the evidence pack so the big block is byte-
            # identical across the fan-out and rides the provider cache
            probe = {k: v for k, v in c.items() if k != "corroborated_by"}
            result, out = await run_agent_step(
                ctx, step_name=f"agent.verify_comment#{i}",
                purpose="Verify one draft review comment against the "
                        "PR-time tree.",
                guidance=_VERIFY_GUIDANCE,
                expected="verdict confirmed|refuted|unverifiable, with "
                         "optional comment/line/severity corrections",
                evidence={"pr_diff": diff_ev,
                          "draft_comment": json.dumps(
                              probe, ensure_ascii=False)},
                output_extension={
                    "verdict": "confirmed|refuted|unverifiable",
                    "comment": "optional tightened rewrite",
                    "line": "optional corrected line number",
                    "severity": "optional corrected severity",
                    "evidence": "confirmed only: verbatim-quoted decisive "
                                "code line(s) with file:line — proof a "
                                "repo-less reader can check"},
                extra_tools=common.get("extra_tools"),
                max_iters=ctx.settings.review_verify_max_iters)
            return i, result, (out or {})

    results = await asyncio.gather(*(_one(i, c)
                                     for i, c in enumerate(comments)))
    demote = {"blocker": "major", "major": "minor", "minor": "nit"}
    kept: list[dict] = []
    n_drop = n_demote = 0
    for i, result, out in sorted(results, key=lambda r: r[0]):
        c = dict(comments[i])
        verdict = str(out.get("verdict") or "").lower()
        if not result.ok or verdict not in ("confirmed", "refuted",
                                            "unverifiable"):
            kept.append(c)          # fail-open: never delete on pass failure
            continue
        if verdict == "refuted":
            n_drop += 1
            continue
        if verdict == "confirmed":
            if out.get("comment"):
                c["comment"] = str(out["comment"])
            if isinstance(out.get("line"), int):
                c["line"] = out["line"]
            sev = str(out.get("severity") or "").lower()
            if sev in _SEVERITY_ORDER:
                c["severity"] = sev
            if out.get("evidence"):
                # replace the drafting-stage narrative with the verifier's
                # quoted proof: the review is judged by readers with no repo
                # access, and a claim whose evidence they can check from the
                # quote alone is the difference between "grounded" and
                # "speculative" (precision sat at .55 across five configs
                # until the rendered evidence became self-proving)
                c["evidence"] = str(out["evidence"])
        else:                        # unverifiable: keep, one step down
            s = str(c.get("severity", "minor")).lower()
            c["severity"] = demote.get(s, "nit")
            n_demote += 1
        kept.append(c)
    ctx.trace.record("review_comments_verified", step="agent.review_diff",
                     total=len(comments), dropped=n_drop, demoted=n_demote)
    out2 = dict(output)
    out2["review_comments"] = kept
    return out2


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
        # checklist resolution: the adapter's knowledge slice first (shared
        # data plane — `knowledge.review_checklist`, relative to the
        # knowledge root, escape-guarded), then the legacy profile/review.md
        # for adapters that still carry one
        candidates: list[Path] = []
        rel = str((adapter.manifest.get("knowledge") or {})
                  .get("review_checklist") or "")
        if rel:
            kroot = Path(ctx.settings.knowledge_dir).resolve()
            kpath = (kroot / rel).resolve()
            if kpath.is_relative_to(kroot):
                candidates.append(kpath)
        candidates.append(adapter.profile_dir / "review.md")
        for review_md in candidates:
            try:
                if review_md.exists() and ctx.settings.profile_briefing_enabled:
                    guidance += ("\n\n## Repo-specific review checklist\n"
                                 + review_md.read_text(encoding="utf-8")[:4_000])
                    break
            except OSError:
                continue

    common = dict(
        step_name="agent.review_diff",
        purpose=f"Review PR #{spec.get('pr')} like an engaged maintainer: "
                "grounded, specific, useful findings.",
        guidance=guidance,
        expected="review_comments with file/line/anchor_snippet/severity/comment/"
                 "evidence; APPROVE-equivalent = empty review_comments with a summary.",
        evidence={"pr_diff": str(diff),
                  "pr_context": ctx.state.get("pr_context", ""),
                  "gate_report": ctx.state.get("gate_report", ""),
                  "sweep_targets": _sweep_targets(str(diff), language),
                  "changed_symbol_consumers": await asyncio.to_thread(
                      _consumer_sweep, _repo_path(ctx), str(diff))},
        output_extension={"review_comments":
                          "list of {file, line, anchor_snippet, severity: "
                          "blocker|major|minor|nit, comment, evidence}"},
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
        ctx.state["_review_depth"] = plan.depth  # MoA eligibility signal (W6)
        if plan.depth == "light":
            # the light tier is the only reviewer surface that ran with no
            # protocol; measured, that cost it ~70% of its anchored findings
            result, output = await run_agent_step(
                ctx, max_iters=ctx.settings.review_light_max_iters,
                **{**common, "guidance": guidance + _REVIEW_LIGHT_PROTOCOL})
            if ctx.settings.review_light_zero_yield_escalate \
                    and not (output.get("review_comments") or []):
                # Silence from the cheapest tier is the one result it is least
                # entitled to. Buy one standard pass rather than ship it — the
                # same reflex as re-asking a zero-yield lens, one tier up.
                ctx.trace.record("review_depth_escalated", step="agent.review_diff",
                                 depth_from="light", depth_to="standard",
                                 reason="light pass returned no findings")
                plan = replace(plan, depth="standard",
                               lens_names=DEFAULT_STANDARD_LENSES,
                               reason=plan.reason + "; escalated: light found nothing")
                ctx.state["_review_depth"] = plan.depth
        if plan.depth != "light":
            if ctx.settings.review_deep_engine:
                # hybrid mode: the planner still owns DEPTH. Deep passes buy
                # per-claim grounding (probe: precision .82 vs baseline .75)
                # but their 4-5 focused findings collapsed val recall to .55;
                # the breadth lenses held recall at .80-.86 but under-ground.
                # Full depth runs both shapes and lets the reducer/verify
                # machinery arbitrate: investigator + adversary for depth,
                # behavior + verification for coverage.
                breadth = [l for l in _REVIEW_LENSES
                           if l["name"] in ("behavior", "verification")]
                passes = (list(_REVIEW_DEEP_PASSES) + breadth
                          if plan.depth == "full"
                          else list(_REVIEW_DEEP_PASSES[:1]) + breadth[:1])
                result, output = await run_agent_step_ensemble(
                    ctx, lenses=passes, merge_key="review_comments",
                    merge_guidance=_REVIEW_MERGE,
                    max_iters=ctx.settings.review_deep_max_iters, **common)
            else:
                lenses = [l for l in _REVIEW_LENSES
                          if l["name"] in plan.lens_names] \
                    or list(_REVIEW_LENSES)
                result, output = await run_agent_step_ensemble(
                    ctx, lenses=lenses, merge_key="review_comments",
                    merge_guidance=_REVIEW_MERGE, **common)
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
    if plan is not None and plan.depth != "light" and result.ok:
        # coverage promotion mines the run's own findings/blockers for
        # uncovered protected-class concerns; runs AFTER the salvage (an
        # ensemble that self-reported needs_review still carries findings
        # worth mining — gating on the pre-salvage status silently disabled
        # the pass on exactly the GT-rich items it exists for) and BEFORE
        # the verify pass, so promoted items face the same scrutiny
        output = await _promote_uncovered(ctx, output, spec)
        # per-comment agentic verification: every surviving draft comment is
        # checked against the PR-time tree by a small tool-loop before the
        # budget — the measured loss driver after the recall fixes was
        # per-comment grounding (val: arm precision .54-.56 vs baseline
        # .65 with recall at parity), which packaging cannot buy
        output = await _verify_comments(ctx, output, common)
    # deterministic comment budget: severity-ordered, corroboration-aware,
    # capped at 6 — the low-signal tail goes first (reducers ignored a
    # prompted cap; the cap is a product budget, so it applies to every
    # depth). The old 5-comment, severity-only cut deleted reducer-KEPT
    # findings that were literal maintainer concerns on large PRs, while
    # 8 + nit-heavy overflow read as noise to the blind judge; 6 kept
    # comments + the promotion pass's protected-class additions is the
    # measured operating point. Within a severity, findings corroborated by
    # more independent lenses go first; the minor-plus overflow tail
    # renders ONLY on evidence-rich reviews (≥2 major/blocker findings) —
    # a quiet PR stays terse (a thin-GT val item rendering 12 findings
    # lost 3/3 on noise).
    comments = sorted(output.get("review_comments") or [],
                      key=lambda c: (_SEVERITY_ORDER.get(
                          str(c.get("severity", "minor")).lower(), 2),
                          -len(c.get("corroborated_by") or [])))
    for c in comments:
        c.pop("corroborated_by", None)
    output["review_comments"] = comments[:8]
    rich = sum(1 for c in comments[:8]
               if _SEVERITY_ORDER.get(str(c.get("severity", "minor")).lower(),
                                      2) <= _SEVERITY_ORDER["major"]) >= 2
    output["_review_overflow"] = [
        c for c in comments[8:]
        if _SEVERITY_ORDER.get(str(c.get("severity", "minor")).lower(), 2)
        <= _SEVERITY_ORDER["minor"]][:4] if rich else []
    if plan is not None:
        result.outputs["review_plan"] = {"depth": plan.depth,
                                         "planner": plan.planner,
                                         "reason": plan.reason}
    if result.ok:
        # Derive each finding's line from its quoted snippet BEFORE rendering: the
        # review body prints `file:line` too, so resolving later (at publish) would
        # show one position in the body and anchor the inline thread at another.
        if output.get("review_comments"):
            resolved, anchor_stats = resolve_review_comments(
                output["review_comments"], str(ctx.state.get("diff_text") or ""))
            output["review_comments"] = resolved
            ctx.trace.record("anchor_resolution", **anchor_stats)
        review_md = _render_review_md(output,
                                      pr_state=str(ctx.state.get("pr_state", "")))
        review_summary = _render_review_summary(
            output, pr_state=str(ctx.state.get("pr_state", "")))
        review_comments = output.get("review_comments") or []
        ctx.state.update({
            "review_text": review_md,
            "review_summary": review_summary,
            "review_comments": review_comments,
        })
        result.outputs["review_text"] = review_md
        result.outputs["review_summary"] = review_summary
        result.outputs["review_comments"] = review_comments
        result.outputs.setdefault("state_updates", {}).update({
            "review_text": review_md,
            "review_summary": review_summary,
            "review_comments": review_comments,
        })
        depth_note = f"; depth={plan.depth} via {plan.planner}" if plan else ""
        result.summary = (f"review produced ({len(output.get('review_comments') or [])} "
                          f"comments{depth_note}) — {result.summary}")
    return result
