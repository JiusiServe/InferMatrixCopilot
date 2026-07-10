"""Review steps: the conditional patch gate and the PR-review agent step.

PR review is eval-informed (see eval/ANALYSIS.md): deterministic gate checks
catch the merge-state/CI issue class no diff-only model caught; evidence-
grounded tool use makes the strongest arm precise; a domain checklist fixes
topicality; a verify-and-rewrite pass fixes actionability. The domain checklist
and the sweep language come from the repo profile (design §V2.2.2), keeping the
core prompt repo-neutral.
"""

from __future__ import annotations

import subprocess

from ...review.diff_summary import build_diff_summary
from ...review.reviewer import run_patch_review
from ...review.triggers import evaluate_triggers
from ...scopes import read_only_scope
from ..step import FailureKind, StepContext, StepResult
from ._common import gh_read_tools as _gh_read_tools
from ._common import repo_path as _repo_path
from ._common import step


@step("review.patch_gate", "validation", "read",
      "Conditional patch review; fail-closed before pushes.",
      patch_review_triggers=("before_push",))
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
                          cwd=str(repo), capture_output=True, text=True, timeout=60).stdout
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


_REVIEW_SYSTEM = """You review pull requests like an engaged maintainer: grounded, \
specific, and useful — real reviewers leave nits and doc asks, not just blockers.

Sweep EVERY item of this checklist. The `sweep_targets` evidence enumerates the diff's \
indexed accesses, new branches, and touched files — your sweep MUST address every listed \
entry relevant to your lens; they were extracted mechanically, so "I didn't notice it" \
is not possible. Record the sweep in the `findings` base field — one line per checklist \
item: what you checked (file read, grep run, or diff hunk) and the result. Complete the \
whole sweep BEFORE writing review_comments; an item with no line in `findings` is a \
missed sweep, and a thin sweep is where reviews silently fail:
1. Correctness of changed logic (None/empty handling, off-by-one, error paths, concurrency).
2. Simplifiability: branches for cases that cannot co-occur, values re-derived by hand \
where an existing helper already provides them (grep the repo for such helpers). The right \
ask for dead or redundant code is REMOVE/simplify it — documenting it is the wrong fix.
3. Breaking behavior: changed defaults or API/protocol shifts — grep for IN-REPO consumers \
(examples, docs, clients, tests, READMEs) that assume the old behavior, then check whether \
THIS diff updates each one; name every consumer left stale.
4. Rebase/merge damage: dropped hunks, duplicated code, references to moved/renamed symbols.
5. Tests & verification: behavior changed without test changes? new skips or loosened \
thresholds justified? For model/pipeline behavior changes, name the specific existing \
test or benchmark that validates the changed path and whether the PR shows it was run.
6. Docs/docstrings/comments made stale or misleading by the change — re-read every \
docstring and doc paragraph in the touched files and check each still tells the truth \
under the NEW behavior.
7. Undocumented assumptions or invariants the change introduces or relies on (ordering, \
"first element is X", implicit units/thresholds) — these deserve a comment or an assert.
8. Scope: files touched beyond the PR's stated purpose.

Severity semantics (they drive the verdict, so assign them honestly):
- blocker: merging as-is causes breakage or data loss.
- major: a real defect, or a consumer/doc/test update this change requires but the diff \
does not contain.
- minor: a concrete improvement that belongs in THIS PR (a simplification, a stale \
docstring fix, a missing assert, a missing verification run).
- nit: optional polish; does NOT block approval.

Then emit review_comments per the output contract:
- Each comment: file, line, severity, WHAT to change and WHY (directive), and the \
evidence you checked.
- EVIDENCE-GROUNDING: every comment must be verifiable from the diff or from repo \
evidence you actually gathered and NAME in the comment (the file you read or grep you \
ran, and what it showed). The comment's FIRST sentence must state the concrete change \
THIS DIFF makes (quote or paraphrase the hunk) — only then the repo-side consequence \
and the directive; a reader holding only the diff must see immediately which change the \
comment hangs on. For comments about diff code, `line` is a line the diff touches; for \
repo-impact comments (a consumer/doc/test elsewhere that this change breaks or leaves \
stale), point file/line at that repo location and quote it.
- A verification ask is a first-class comment when it names the exact test/benchmark \
command and the specific regression risk it guards; bare process asks ("run the tests") \
are still banned.
- Behavior/correctness findings outrank documentation asks: at most 2 comments whose only \
ask is adding a comment or docstring.
- A suspicion you could NOT verify goes in the `findings` base field, NEVER in \
review_comments — a posted review comment must stand on checked evidence.
- No praise-only comments. At most 6 comments.
- Only if the sweep truly surfaces nothing that belongs in this PR: empty review_comments \
with a one-line summary."""

# Perspective-diverse ensemble lenses (run_agent_step_ensemble): each sample
# goes DEEP on a slice of the checklist instead of sampling one corner of all
# of it — the eval showed single runs collapse into whichever failure mode the
# first finding anchors (e.g. all-doc-nits), while unions across runs hit 5/8
# ground-truth issues. Lenses run concurrently, so a finer decomposition costs
# tokens but no wall-clock.
_REVIEW_LENSES = [
    {"name": "logic",
     "focus": "Checklist items 1, 2 and 4, as a MECHANICAL SWEEP OF THE DIFF: "
              "for EVERY hunk, in order, ask (a) can the new branches/"
              "conditions actually all occur — a branch for a case that "
              "cannot co-occur is a finding whose fix is REMOVE/simplify, "
              "never document; (b) does the new code re-derive by hand a "
              "value an existing helper provides (grep the repo for the "
              "computation before flagging); (c) None/empty handling, "
              "off-by-one, error paths; (d) rebase/merge damage (duplicated "
              "code, moved/renamed symbols). Work hunk by hunk; do not skip "
              "any. Use repo tools only to CONFIRM a suspicion from the "
              "diff."},
    {"name": "behavior",
     "focus": "Checklist item 3, diff-first: for EVERY hunk that changes a "
              "default, API, protocol or output format, list who depends on "
              "the OLD behavior — grep the repo for in-repo consumers "
              "(examples/, docs/, clients, tests, READMEs) — then check "
              "whether THIS diff updates each one; name every consumer left "
              "stale, quoting it. If the diff changes no default/API, say so "
              "and report nothing for this item."},
    {"name": "contracts",
     "focus": "Checklist items 6 and 7, as a MECHANICAL SWEEP OF THE TOUCHED "
              "FILES: (a) enumerate EVERY docstring, inline comment, and "
              "field description in each touched file that the change makes "
              "stale or misleading — verify each still tells the truth under "
              "the NEW behavior, quoting any that don't (stopping after the "
              "first is the most common failure); (b) for EVERY indexed or "
              "first-element access the diff adds (xs[0], 'first element is "
              "X', ordering, implicit units/thresholds), state the "
              "assumption it encodes and what guarantees it — if nothing "
              "does, ask for an assert or comment."},
    {"name": "verification",
     "focus": "Checklist item 5, diff-first: for EVERY behavior-changing "
              "hunk, name the specific existing test or benchmark that "
              "exercises the changed path (grep tests/, benchmarks/ for the "
              "touched symbols). Behavior changed with no test change, a "
              "changed path no test exercises, new skips, or loosened "
              "thresholds are findings. If the PR gives no sign the relevant "
              "test/benchmark was run, ask for exactly that run/extension, "
              "citing the concrete regression risk it guards."},
]

_REVIEW_MERGE = (
    "Severity semantics: blocker = breaks on merge; major = defect or "
    "required update the diff lacks; minor = concrete change that belongs in "
    "THIS PR; nit = optional polish. Severities above nit request changes — "
    "demote to nit anything genuinely optional; a VERIFIED but optional "
    "comment is demoted, not dropped. Drop comments whose evidence is "
    "UNVERIFIED unless a second lens corroborates them. When you rewrite a "
    "comment, its "
    "FIRST sentence must state the concrete change the diff makes (quote or "
    "paraphrase the hunk) — for repo-impact comments too, where the "
    "consequence elsewhere (named consumer/doc/test file, quoted) comes "
    "second. Comments about diff code must point `line` at a line the diff "
    "touches. A verification ask that names the exact test/benchmark "
    "command and the concrete regression risk it guards is a first-class "
    "comment, not a process nit.")

_SEVERITY_ORDER = {"blocker": 0, "major": 1, "minor": 2, "nit": 3}


def _sweep_targets(diff: str, language: str = "python") -> str:
    """Deterministic sweep targets extracted from the diff's added lines.

    Injected as evidence so lens coverage of the ENUMERABLE classes (index
    assumptions, new branches, untested files) never depends on the model
    enumerating the diff itself — stochastic self-enumeration was the
    highest-variance link in review recall (whole classes silently skipped
    on some runs).

    The line-level extractors are language-keyed (from the repo profile);
    an unknown language degrades to the file-level sections only — recorded
    honestly instead of running Python heuristics on foreign syntax."""
    import re

    from ...profiles.languages import sweep_re
    rules = sweep_re(language)
    current: str | None = None
    new_line = 0
    subs: list[str] = []
    branches: list[str] = []
    files: set[str] = set()
    test_files: set[str] = set()
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            files.add(current)
            if current.startswith("tests/") or "/tests/" in current:
                test_files.add(current)
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            new_line = int(m.group(1)) if m else 0
        elif current and line.startswith("+") and not line.startswith("+++"):
            code = line[1:]
            stripped = code.strip()
            if rules is not None:
                if rules[0].search(code):
                    subs.append(f"{current}:{new_line} `{stripped[:90]}`")
                if rules[1].match(stripped):
                    branches.append(f"{current}:{new_line} `{stripped[:90]}`")
            new_line += 1
        elif current and not line.startswith("-"):
            new_line += 1
    non_test = sorted(f for f in files if f not in test_files)
    out: list[str] = []
    if subs:
        out.append("INDEXED/FIRST-ELEMENT ACCESSES ADDED — contracts lens "
                   "must state the assumption + what guarantees it for EACH:")
        out += [f"- {s}" for s in subs[:20]]
    if branches:
        out.append("NEW/CHANGED BRANCHES — logic lens must answer for EACH: "
                   "can all arms occur? dead/redundant?")
        out += [f"- {b}" for b in branches[:25]]
    if non_test:
        out.append("NON-TEST FILES TOUCHED — verification lens must name the "
                   "test/benchmark covering each changed path:")
        out += [f"- {f}" for f in non_test[:20]]
    out.append("TEST FILES TOUCHED IN THIS DIFF: "
               + (", ".join(sorted(test_files)) or "NONE"))
    return "\n".join(out)


def _render_review_md(output: dict) -> str:
    comments = sorted(output.get("review_comments") or [],
                      key=lambda c: _SEVERITY_ORDER.get(
                          str(c.get("severity", "minor")).lower(), 2))
    lines = []
    for c in comments:
        loc = f"`{c.get('file', '?')}:{c.get('line', '?')}`"
        ev = f" (evidence: {c['evidence']})" if c.get("evidence") else ""
        lines.append(f"{loc} [{c.get('severity', 'minor')}] — "
                     f"{c.get('comment', '')}{ev}")
    # verdict coherence: severities above nit mean "belongs in THIS PR", and
    # asking for in-PR changes while approving is incoherent (the eval's
    # decision metric caught exactly that: all-minor reviews said APPROVE on
    # PRs whose human maintainers requested changes)
    blocking = any(str(c.get("severity", "")).lower()
                   in ("blocker", "major", "minor") for c in comments)
    verdict = "REQUEST CHANGES" if blocking else "APPROVE"
    body = "\n\n".join(lines) if lines else output.get("summary", "No findings.")
    return f"{body}\n\n**Verdict:** {verdict}"


@step("agent.review_diff", "agent", "read",
      "Evidence-grounded two-stage review: tool-loop investigation draft, "
      "then verify-and-rewrite editor pass.",
      tool_scope=read_only_scope())
async def _review_diff(ctx: StepContext) -> StepResult:
    """PR review as a governed agent step (unified runtime): evidence pack,
    skill retrieval, enforced read-only tools, structured review_comments.
    By default runs as a 3-lens ensemble with verify-and-merge (robustness:
    single runs have high variance; see eval/ANALYSIS.md)."""
    from ..agent_runtime import _resolve_plugin, run_agent_step, run_agent_step_ensemble

    diff = ctx.state.get("diff_text", "")
    if not diff:
        return StepResult(False, FailureKind.BLOCKED, "no diff_text in state")
    spec = ctx.state.get("task_spec") or {}

    # repo knowledge from the profile, not the core (design §V2.2.2): domain
    # checklist extension + the language key for the sweep extractors
    plugin = _resolve_plugin(ctx)
    language = "python"
    guidance = _REVIEW_SYSTEM
    if plugin is not None:
        language = str(plugin.manifest.get("repo", {}).get("language")
                       or "python")
        review_md = plugin.profile_dir / "review.md"
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
    if ctx.settings.review_ensemble:
        result, output = await run_agent_step_ensemble(
            ctx, lenses=_REVIEW_LENSES, merge_key="review_comments",
            merge_guidance=_REVIEW_MERGE, **common)
        # deterministic comment budget: severity-ordered, capped at 5 — the
        # low-signal tail goes first (reducers ignored a prompted cap)
        comments = sorted(output.get("review_comments") or [],
                          key=lambda c: _SEVERITY_ORDER.get(
                              str(c.get("severity", "minor")).lower(), 2))
        output["review_comments"] = comments[:5]
    else:
        result, output = await run_agent_step(ctx, **common)
    if result.ok:
        review_md = _render_review_md(output)
        ctx.state["review_text"] = review_md
        result.outputs["review_text"] = review_md[:4_000]
        result.outputs.setdefault("state_updates", {})["review_text"] = review_md
        result.summary = (f"review produced ({len(output.get('review_comments') or [])} "
                          f"comments) — {result.summary}")
    return result
