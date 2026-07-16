"""Issue-facing steps: fetch, drafted answer, triage table, gated posting."""

from __future__ import annotations

import json

from ..step import FailureKind, StepContext, StepResult, StepSpec
from ._common import from_state, register_step, require_repo, step
from ._common import gh as _gh
from ._common import gh_read_tools as _gh_read_tools
from ._common import post_step as _post_step
from ._common import repo_path as _repo_path


@step("issue.fetch", "deterministic", "read",
      "Fetch an issue via gh (read-only).")
async def _issue_fetch(ctx: StepContext) -> StepResult:
    """Fetch issue material via `gh` for the downstream answer/triage agents.
    Reads `task_spec`: with an `issue` number, fetches that one issue
    (`issue view` — title/body/labels/comments); with no number but
    `kind == "issue_filter"`, fetches recent open issues (`issue list`, capped by
    `params.limit`) for triage mode; any other no-number case is BLOCKED. Returns
    injected `issue_text` from state verbatim when present (offline testing); a
    failed `gh` call degrades to BLOCKED.

    Publishes the raw JSON as `issue_text` to state (B2 `state_updates`)."""
    cached = from_state(ctx, "issue_text")
    if cached is not None:
        return cached
    spec = ctx.state.get("task_spec") or {}
    issue = spec.get("issue") if isinstance(spec, dict) else None
    kind = spec.get("kind") if isinstance(spec, dict) else ""
    repo = require_repo(ctx)
    if isinstance(repo, StepResult):
        return repo
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


def _issue_agent_step(step_name: str, purpose: str, guidance: str,
                      extension: dict, render):
    """Issue-facing agent steps on the unified runtime (修正方案 P1)."""

    async def handler(ctx: StepContext) -> StepResult:
        """Run the configured issue agent step on the unified runtime, reading
        `issue_text` from state as evidence (BLOCKED when absent) and granting the
        read-only gh tools. On success, `render` turns the agent output into a
        (state key, text) pair which is stored and published (B2 `state_updates`,
        e.g. `draft_answer` / `triage_table`); the draft is never auto-posted."""
        from ..agent_runtime import run_agent_step

        material = ctx.state.get("issue_text", "")
        if not material:
            return StepResult(False, FailureKind.BLOCKED, "no issue_text in state")
        result, output = await run_agent_step(
            ctx, step_name=step_name, purpose=purpose, guidance=guidance,
            evidence={"issue_text": str(material)},
            output_extension=extension,
            extra_tools=_gh_read_tools(_repo_path(ctx)),
            max_iters=ctx.settings.max_agent_iters,  # T3: the default review
            # budget left ~zero headroom for grep-heavy triage (issue4842
            # blocked 2/3 replicates at the cap)
        )
        if result.ok:
            key, text = render(output)
            ctx.state[key] = text
            result.outputs[key] = text
            result.outputs.setdefault("state_updates", {})[key] = text
            result.summary = f"{key} produced — {result.summary}"
        elif result.failure is FailureKind.ESCALATE:
            # An incomplete-but-substantive draft ships with caveats instead of
            # being discarded (eval: 3 escalated runs held correct diagnoses and
            # delivered nothing). Empty/thin drafts still escalate. The prose
            # floor alone is wrong for triage: a complete one-row triage table
            # renders under 200 chars, so structured rows count as substantive
            # on their own (a high-confidence needs_review triage of issue5123
            # was discarded and blocked the run).
            key, text = render(output)
            if output.get("triage_table") or len(text.strip()) > 300:
                text = (f"> ⚠ draft shipped with caveats — agent self-assessed "
                        f"confidence: {output.get('confidence', 'low')}; "
                        f"verify before relying on it.\n\n{text}")
                ctx.state[key] = text
                result = StepResult(
                    True, summary=f"{key} produced with caveats — {result.summary}",
                    outputs={**result.outputs, key: text},
                    changed_files=result.changed_files)
                result.outputs.setdefault("state_updates", {})[key] = text
        return result

    return handler


def _render_answer(output: dict) -> tuple[str, str]:
    """Render the draft-answer agent output into the `("draft_answer", text)`
    pair: `answer_draft`, else the salvaged raw final text, else `summary`.
    Appends the `disposition` slot (close/keep-open/duplicate/reopen-when —
    T3 forensics #8: completeness losses were missing closing moves) and an
    epistemics caveat when merge-state claims lack a gh verification call
    (forensics #7)."""
    text = str(output.get("answer_draft") or output.get("_raw_text")
               or output.get("summary", ""))
    disp = str(output.get("disposition") or "").strip()
    if disp and disp.lower() not in text.lower():
        text += f"\n\n**Disposition:** {disp}"
    tools_used = output.get("_tools_used") or []
    lowered = text.lower()
    if (("merged" in lowered or "on main" in lowered)
            and "gh_pr_view" not in tools_used):
        text += ("\n\n> ⚠ merge-state statements above were not verified via "
                 "gh this run — treat as unconfirmed.")
    return "draft_answer", text


def _render_triage(output: dict) -> tuple[str, str]:
    """Render the triage agent's `triage_table` rows into the
    `("triage_table", markdown)` pair — a markdown table (issue/type/module/
    priority/labels). Falls back to the agent's `summary` when there are no rows."""
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


register_step(StepSpec(
    "agent.draft_issue_answer", "agent", "read",
    _issue_agent_step(
        "agent.draft_issue_answer",
        "Draft a helpful, factual answer to the repository issue.",
        "Ground every claim in the issue text or code you actually "
        "read (use your repo tools). Never invent APIs; say plainly "
        "when unsure. The draft is never auto-posted.",
        {"answer_draft": "the complete draft reply (markdown)",
         "disposition": "close / keep-open / duplicate-of-#N / needs-info — "
                        "match the thread's last maintainer action; include "
                        "the reopen condition"},
        _render_answer),
    "Draft an issue answer (governed agent step; never auto-posted)."))

register_step(StepSpec(
    "agent.triage_issues", "agent", "read",
    _issue_agent_step(
        "agent.triage_issues",
        "Triage the GitHub issues: classify each and route it.",
        "For each issue: type (bug/feature/question), affected "
        "module (verify module paths with repo tools when unsure), "
        "priority, suggested labels.",
        {"triage_table":
         "list of {number, title, type, module, priority, labels}"},
        _render_triage),
    "Classify/label/route issues (governed agent step, read-only)."))

register_step(StepSpec(
    "issue.post_answer", "script", "push",
    _post_step("draft_answer",
               lambda spec, body: ["issue", "comment", str(spec.get("issue")),
                                    "--body", body],
               "issue answer"),
    "Post the drafted answer (explicit post flag + ALLOW_POST)."))
