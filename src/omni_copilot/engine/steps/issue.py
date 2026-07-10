"""Issue-facing steps: fetch, drafted answer, triage table, gated posting."""

from __future__ import annotations

import json

from ...scopes import read_only_scope
from ..step import FailureKind, StepContext, StepResult, StepSpec
from ._common import gh as _gh
from ._common import gh_read_tools as _gh_read_tools
from ._common import post_step as _post_step
from ._common import register_step
from ._common import repo_path as _repo_path
from ._common import step


@step("issue.fetch", "deterministic", "read",
      "Fetch an issue via gh (read-only).")
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


def _issue_agent_step(step_name: str, purpose: str, guidance: str,
                      extension: dict, render):
    """Issue-facing agent steps on the unified runtime (修正方案 P1)."""

    async def handler(ctx: StepContext) -> StepResult:
        from ..agent_runtime import run_agent_step

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


register_step(StepSpec(
    "agent.draft_issue_answer", "agent", "read",
    _issue_agent_step(
        "agent.draft_issue_answer",
        "Draft a helpful, factual answer to the repository issue.",
        "Ground every claim in the issue text or code you actually "
        "read (use your repo tools). Never invent APIs; say plainly "
        "when unsure. The draft is never auto-posted.",
        {"answer_draft": "the complete draft reply (markdown)"},
        _render_answer),
    "Draft an issue answer (governed agent step; never auto-posted).",
    read_only_scope()))

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
    "Classify/label/route issues (governed agent step, read-only).",
    read_only_scope()))

register_step(StepSpec(
    "issue.post_answer", "script", "push",
    _post_step("draft_answer",
               lambda spec, body: ["issue", "comment", str(spec.get("issue")),
                                    "--body", body],
               "issue answer"),
    "Post the drafted answer (explicit post flag + ALLOW_POST)."))
