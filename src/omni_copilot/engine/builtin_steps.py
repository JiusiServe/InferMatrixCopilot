"""Builtin step library — vetted engineering actions the planner may compose.

Wrap-don't-rewrite: the locked repo-rebase playbook delegates to the existing
5-phase orchestrator (`rebase.run_external`) instead of reimplementing it.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..review.diff_summary import build_diff_summary
from ..review.reviewer import run_patch_review
from ..review.triggers import evaluate_triggers
from ..scopes import read_only_scope
from ..targets.base import PushPolicy, guard_push
from .registry import StepRegistry
from .step import FailureKind, StepContext, StepResult, StepSpec


def _repo_path(ctx: StepContext) -> Path | None:
    p = ctx.params.get("repo_path") or ctx.state.get("repo_path")
    return Path(p) if p else None


async def _guard_clean(ctx: StepContext) -> StepResult:
    repo = _repo_path(ctx)
    if repo is None or not repo.exists():
        return StepResult(False, FailureKind.BLOCKED, f"repo path missing: {repo}")
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


async def _diff_summary(ctx: StepContext) -> StepResult:
    repo = _repo_path(ctx)
    if repo is None:
        return StepResult(False, FailureKind.BLOCKED, "no repo path")
    summary = build_diff_summary(
        repo, base_ref=ctx.params.get("base_ref", "HEAD"),
        primary_files=tuple(ctx.state.get("primary_files", ())), trace=ctx.trace,
    )
    return StepResult(True, summary=f"{len(summary.changed_files)} files, "
                                    f"+{summary.insertions}/-{summary.deletions}",
                      outputs={"diff_summary": summary.__dict__})


async def _run_external_rebase(ctx: StepContext) -> StepResult:
    """Delegate to the existing 5-phase orchestrator (locked pipeline, zero
    regression) — monitored: per-phase/per-module progress is streamed from the
    parent's state.json into the RunTrace, and failures are classified + turned
    into escalation material (the parent pipeline sends no notifications)."""
    import asyncio as _asyncio

    from ..rebase.monitor import (build_command, build_escalation, classify_failure,
                                  diff_progress, parse_parent_state, summarize_progress)

    spec = ctx.state.get("task_spec") or {}
    task_params = (spec.get("params") if isinstance(spec, dict) else {}) or {}
    resuming = bool(ctx.state.get("resuming"))
    cmd = build_command(ctx.params.get("command") or ctx.settings.rebase_orchestrator_cmd,
                        task_params, resuming=resuming)
    state_file = Path(ctx.params.get("state_file")
                      or ctx.settings.rebase_agent_root / "rebase_logs" / "state.json")
    poll = float(ctx.params.get("poll_interval") or ctx.settings.rebase_poll_interval)
    timeout = float(ctx.params.get("timeout", 6 * 3600))
    ctx.trace.record("external_command", command=cmd)

    pre = parse_parent_state(state_file)
    if pre and pre.get("phase") not in ("", "done", None) and not resuming:
        ctx.trace.record("rebase_preexisting_state", phase=pre.get("phase"),
                         run_id=pre.get("run_id"))

    ctx.run_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = ctx.run_dir / "orchestrator_stdout.log"
    stderr_path = ctx.run_dir / "orchestrator_stderr.log"
    status_path = ctx.run_dir / "rebase_status.json"
    timed_out = False
    with stdout_path.open("ab") as out_f, stderr_path.open("ab") as err_f:
        try:
            proc = await _asyncio.create_subprocess_exec(*cmd, stdout=out_f, stderr=err_f)
        except FileNotFoundError:
            return StepResult(False, FailureKind.BLOCKED,
                              f"orchestrator not found: {cmd[0]!r} — is "
                              "vllm-omni-rebase-agent installed?")
        last = summarize_progress(parse_parent_state(state_file))
        loop = _asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while proc.returncode is None:
            try:
                await _asyncio.wait_for(proc.wait(), timeout=min(poll, 5.0))
                break
            except _asyncio.TimeoutError:
                pass
            if loop.time() > deadline:
                proc.terminate()
                try:
                    await _asyncio.wait_for(proc.wait(), timeout=30)
                except _asyncio.TimeoutError:
                    proc.kill()
                timed_out = True
                break
            current = summarize_progress(parse_parent_state(state_file))
            events = diff_progress(last, current)
            if events:
                ctx.trace.record("rebase_progress", events=events,
                                 phase=current.get("phase"))
                status_path.write_text(json.dumps(current, indent=2))
                last = current

    final_state = parse_parent_state(state_file)
    rc_early = proc.returncode if proc.returncode is not None else 1
    if rc_early != 0 and final_state == pre:
        # state.json never changed during THIS invocation — whatever it says
        # belongs to a previous run; don't let a stale phase=done mask a crash
        final_state = None
    final = summarize_progress(final_state)
    status_path.write_text(json.dumps(final, indent=2))
    tail = ""
    for p in (stderr_path, stdout_path):
        try:
            tail = tail or p.read_text(encoding="utf-8", errors="replace")[-3_000:].strip()
        except OSError:
            pass

    rc = proc.returncode if proc.returncode is not None else 1
    kind, note = classify_failure(rc, final_state, timed_out=timed_out)
    if kind is None:
        summary = f"external rebase pipeline completed ({note}; phase={final.get('phase')})"
        return StepResult(True, summary=summary,
                          outputs={"rebase_status": final, "tail": tail})
    esc = build_escalation(final_state, ctx.settings.rebase_agent_root)
    return StepResult(False, kind, f"{note} (exit {rc})",
                      outputs={**esc, "rebase_status": final, "tail": tail})


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


async def _push(ctx: StepContext) -> StepResult:
    repo = _repo_path(ctx)
    raw = ctx.state.get("push_policy")
    policy = raw if isinstance(raw, PushPolicy) else PushPolicy(**(raw or {}))
    protected = ctx.state.get("protected_branches") or ctx.settings.protected_branches
    ctx.trace.record("push_requested", remote=policy.remote, branch=policy.branch)
    decision = guard_push(policy, list(protected))
    if not decision.allowed:
        return StepResult(False, FailureKind.FORBIDDEN, decision.reason)
    if not ctx.settings.allow_push:
        return StepResult(True, summary=f"dry-run (ALLOW_PUSH=0): {' '.join(decision.command)}",
                          outputs={"dry_run": True, "command": list(decision.command)})
    out = subprocess.run(list(decision.command), cwd=str(repo), capture_output=True,
                         text=True, timeout=300)
    if out.returncode != 0:
        return StepResult(False, FailureKind.ESCALATE,
                          f"push failed: {out.stderr[-1_000:]}")
    return StepResult(True, summary=f"pushed {policy.remote} HEAD:{policy.branch}")


async def _final_report(ctx: StepContext) -> StepResult:
    lines = ["# Run report", ""]
    spec = ctx.state.get("task_spec")
    if spec:
        lines += [f"- task: {spec}", ""]
    for step_id, outputs in (ctx.state.get("outputs") or {}).items():
        lines.append(f"## {step_id}")
        for k, v in (outputs or {}).items():
            lines.append(f"- **{k}**: {str(v)[:2_000]}")
        lines.append("")
    path = ctx.run_dir / "RUN_REPORT.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return StepResult(True, summary=f"report written: {path}",
                      outputs={"report": str(path)})


# -- read-only GitHub-facing steps (L2 palette) --------------------------------

def _gh(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        out = subprocess.run(["gh", *args], cwd=str(cwd) if cwd else None,
                             capture_output=True, text=True, timeout=120)
        return out.returncode, out.stdout or out.stderr
    except FileNotFoundError:
        return 127, "gh CLI not installed"


async def _pr_fetch_diff(ctx: StepContext) -> StepResult:
    if "diff_text" in ctx.state:  # injected (tests / offline)
        return StepResult(True, summary="diff from state",
                          outputs={"chars": len(ctx.state["diff_text"]),
                                   "state_updates": {"diff_text": ctx.state["diff_text"]}})
    spec = ctx.state.get("task_spec") or {}
    pr = spec.get("pr") if isinstance(spec, dict) else None
    repo = _repo_path(ctx)
    if not pr:
        return StepResult(False, FailureKind.BLOCKED, "no PR number in task spec")
    if repo is None or not repo.exists():
        return StepResult(False, FailureKind.BLOCKED,
                          f"repo checkout not configured (repo_path={repo}) — set "
                          "REPO_PATHS in .env or a plugin repo.path")
    code, out = _gh(["pr", "diff", str(pr)], cwd=repo)
    if code != 0:
        return StepResult(False, FailureKind.BLOCKED, f"gh pr diff failed: {out[:500]}")
    ctx.state["diff_text"] = out
    return StepResult(True, summary=f"fetched PR #{pr} diff ({len(out)} chars)",
                      outputs={"state_updates": {"diff_text": out}})


async def _issue_fetch(ctx: StepContext) -> StepResult:
    if "issue_text" in ctx.state:
        return StepResult(True, summary="issue from state",
                          outputs={"state_updates": {"issue_text": ctx.state["issue_text"]}})
    spec = ctx.state.get("task_spec") or {}
    issue = spec.get("issue") if isinstance(spec, dict) else None
    kind = spec.get("kind") if isinstance(spec, dict) else ""
    repo = _repo_path(ctx)
    if repo is None or not repo.exists():
        return StepResult(False, FailureKind.BLOCKED,
                          f"repo checkout not configured (repo_path={repo}) — set "
                          "REPO_PATHS in .env or a plugin repo.path")
    if not issue:
        if kind != "issue_filter":
            return StepResult(False, FailureKind.BLOCKED, "no issue number in task spec")
        # triage mode: recent open issues instead of a single one
        limit = str(ctx.params.get("limit", 20))
        code, out = _gh(["issue", "list", "--state", "open", "--limit", limit,
                         "--json", "number,title,labels,createdAt"], cwd=repo)
        if code != 0:
            return StepResult(False, FailureKind.BLOCKED, f"gh issue list failed: {out[:500]}")
        ctx.state["issue_text"] = out
        n = len(json.loads(out or "[]"))
        return StepResult(True, summary=f"fetched {n} open issues for triage",
                          outputs={"state_updates": {"issue_text": out}})
    code, out = _gh(["issue", "view", str(issue), "--json",
                     "title,body,labels,comments"], cwd=repo)
    if code != 0:
        return StepResult(False, FailureKind.BLOCKED, f"gh issue view failed: {out[:500]}")
    ctx.state["issue_text"] = out
    return StepResult(True, summary=f"fetched issue #{issue}",
                      outputs={"state_updates": {"issue_text": out}})


# -- PR review (eval-informed; see eval/ANALYSIS.md) ---------------------------
# Findings applied: deterministic gate checks catch the merge-state/CI issue
# class no model caught; evidence-grounded tool use is what made the strongest
# arm precise; a domain checklist fixes topicality; a verify-and-rewrite pass
# fixes actionability (the skill-injected arm's weakest score).

_REVIEW_SYSTEM = """You review vLLM-Omni pull requests like an engaged maintainer: grounded, \
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


def _sweep_targets(diff: str) -> str:
    """Deterministic sweep targets extracted from the diff's added lines.

    Injected as evidence so lens coverage of the ENUMERABLE classes (index
    assumptions, new branches, untested files) never depends on the model
    enumerating the diff itself — stochastic self-enumeration was the
    highest-variance link in review recall (whole classes silently skipped
    on some runs)."""
    import re

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
            if re.search(r"\w\[\s*0\s*\]|\.pop\(0\)|next\(iter\(", code):
                subs.append(f"{current}:{new_line} `{stripped[:90]}`")
            if re.match(r"(el)?if\b|else\b", stripped):
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


def _gh_read_tools(repo: Path | None) -> dict:
    """Read-only gh tools for agent steps (int-coerced args — no injection)."""
    from ..tools import ToolDef

    def _view(kind: str, number, fields: str) -> str:
        code, out = _gh([kind, "view", str(int(number)), "--json", fields],
                        cwd=repo)
        return out[:15_000] if code == 0 else f"gh failed: {out[:400]}"

    def gh_pr_view(pr, **_: object) -> str:
        return _view("pr", pr, "title,body,state,isDraft,mergeable,files")

    def gh_issue_view(issue, **_: object) -> str:
        return _view("issue", issue, "title,body,labels,comments")

    def gh_ci_read(pr, **_: object) -> str:
        code, out = _gh(["pr", "checks", str(int(pr)), "--json",
                         "name,state,bucket"], cwd=repo)
        return out[:10_000] if code == 0 else f"gh failed: {out[:400]}"

    n = {"type": "integer"}
    return {
        "gh_pr_view": ToolDef("gh_pr_view", "Read PR metadata (read-only).",
                              {"type": "object", "properties": {"pr": n},
                               "required": ["pr"]}, gh_pr_view),
        "gh_issue_view": ToolDef("gh_issue_view", "Read an issue (read-only).",
                                 {"type": "object", "properties": {"issue": n},
                                  "required": ["issue"]}, gh_issue_view),
        "gh_ci_read": ToolDef("gh_ci_read", "Read a PR's CI checks (read-only).",
                              {"type": "object", "properties": {"pr": n},
                               "required": ["pr"]}, gh_ci_read),
    }


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


async def _review_diff(ctx: StepContext) -> StepResult:
    """PR review as a governed agent step (unified runtime): evidence pack,
    skill retrieval, enforced read-only tools, structured review_comments.
    By default runs as a 3-lens ensemble with verify-and-merge (robustness:
    single runs have high variance; see eval/ANALYSIS.md)."""
    from .agent_runtime import run_agent_step, run_agent_step_ensemble

    diff = ctx.state.get("diff_text", "")
    if not diff:
        return StepResult(False, FailureKind.BLOCKED, "no diff_text in state")
    spec = ctx.state.get("task_spec") or {}
    common = dict(
        step_name="agent.review_diff",
        purpose=f"Review PR #{spec.get('pr')} like an engaged maintainer: "
                "grounded, specific, useful findings.",
        guidance=_REVIEW_SYSTEM,
        expected="review_comments with file/line/severity/comment/evidence; "
                 "APPROVE-equivalent = empty review_comments with a summary.",
        evidence={"pr_diff": str(diff),
                  "gate_report": ctx.state.get("gate_report", ""),
                  "sweep_targets": _sweep_targets(str(diff))},
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


async def _pr_gate_check(ctx: StepContext) -> StepResult:
    """Deterministic gate check: draft/merge-state/failing checks — the issue
    class the eval showed no diff-only reviewer catches. Non-blocking: the
    findings go into the review context and the report."""
    if "gate_report" in ctx.state:  # injected (tests / offline)
        return StepResult(True, summary="gate report from state",
                          outputs={"state_updates": {"gate_report": ctx.state["gate_report"]}})
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


def _issue_agent_step(step_name: str, purpose: str, guidance: str,
                      extension: dict, render):
    """Issue-facing agent steps on the unified runtime (修正方案 P1)."""

    async def handler(ctx: StepContext) -> StepResult:
        from .agent_runtime import run_agent_step

        material = ctx.state.get("issue_text", "")
        if not material:
            return StepResult(False, FailureKind.BLOCKED, "no issue_text in state")
        result, output = await run_agent_step(
            ctx, step_name=step_name, purpose=purpose, guidance=guidance,
            evidence={"issue_text": str(material)},
            output_extension=extension,
            extra_tools=_gh_read_tools(_repo_path(ctx)),
        )
        if result.ok:
            key, text = render(output)
            ctx.state[key] = text
            result.outputs[key] = text[:4_000]
            result.outputs.setdefault("state_updates", {})[key] = text
            result.summary = f"{key} produced — {result.summary}"
        return result

    return handler


def _render_answer(output: dict) -> tuple[str, str]:
    return "draft_answer", str(output.get("answer_draft")
                               or output.get("summary", ""))


def _render_triage(output: dict) -> tuple[str, str]:
    rows = output.get("triage_table") or []
    if not rows:
        return "triage_table", str(output.get("summary", ""))
    lines = ["| Issue | Type | Module | Priority | Labels |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| #{r.get('number', '?')} {str(r.get('title', ''))[:60]} | "
                     f"{r.get('type', '?')} | {r.get('module', '?')} | "
                     f"{r.get('priority', '?')} | "
                     f"{', '.join(r.get('labels') or [])} |")
    return "triage_table", "\n".join(lines)


def register_builtin_steps(registry: StepRegistry) -> StepRegistry:
    add = registry.register
    add(StepSpec("workspace.guard_clean", "deterministic", "read", _guard_clean,
                 "Refuse to start on a dirty working tree."))
    add(StepSpec("analysis.diff_summary", "deterministic", "read", _diff_summary,
                 "Cheap diffstat + out-of-scope/full-write flags."))
    add(StepSpec("rebase.run_external", "script", "write_workspace", _run_external_rebase,
                 "Delegate to the existing 5-phase rebase orchestrator (locked pipeline)."))
    add(StepSpec("review.patch_gate", "validation", "read", _patch_gate,
                 "Conditional patch review; fail-closed before pushes.",
                 patch_review_triggers=("before_push",)))
    add(StepSpec("ci.push", "script", "push", _push,
                 "Guarded push (PushPolicy AND protected branches; dry-run default)."))
    add(StepSpec("report.final_summary", "report", "report", _final_report,
                 "Write RUN_REPORT.md from accumulated step outputs."))
    add(StepSpec("pr.fetch_diff", "deterministic", "read", _pr_fetch_diff,
                 "Fetch a PR diff via gh (read-only)."))
    add(StepSpec("issue.fetch", "deterministic", "read", _issue_fetch,
                 "Fetch an issue via gh (read-only)."))
    add(StepSpec("pr.gate_check", "deterministic", "read", _pr_gate_check,
                 "Draft/merge-state/failing-checks gate report (deterministic)."))
    add(StepSpec("agent.review_diff", "agent", "read", _review_diff,
                 "Evidence-grounded two-stage review: tool-loop investigation "
                 "draft, then verify-and-rewrite editor pass.",
                 tool_scope=read_only_scope()))
    add(StepSpec("agent.draft_issue_answer", "agent", "read",
                 _issue_agent_step(
                     "agent.draft_issue_answer",
                     "Draft a helpful, factual answer to the vLLM-Omni issue.",
                     "Ground every claim in the issue text or code you actually "
                     "read (use your repo tools). Never invent APIs; say plainly "
                     "when unsure. The draft is never auto-posted.",
                     {"answer_draft": "the complete draft reply (markdown)"},
                     _render_answer),
                 "Draft an issue answer (governed agent step; never auto-posted).",
                 tool_scope=read_only_scope()))
    add(StepSpec("agent.triage_issues", "agent", "read",
                 _issue_agent_step(
                     "agent.triage_issues",
                     "Triage the GitHub issues: classify each and route it.",
                     "For each issue: type (bug/feature/question), affected "
                     "module (verify module paths with repo tools when unsure), "
                     "priority, suggested labels.",
                     {"triage_table":
                      "list of {number, title, type, module, priority, labels}"},
                     _render_triage),
                 "Classify/label/route issues (governed agent step, read-only).",
                 tool_scope=read_only_scope()))

    from .pr_steps import register_pr_steps  # late import: pr_steps imports helpers above
    from .rebase_native_steps import register_rebase_native_steps

    register_pr_steps(registry)
    register_rebase_native_steps(registry)
    return registry
