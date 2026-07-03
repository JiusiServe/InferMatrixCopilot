"""Patch Review agent — READ-ONLY reviewer of the actual diff.

Fail-closed: when no reviewer LLM is available the verdict is `unavailable`,
which push gates must treat as not-passing (escalate, don't ship).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..llm import LLM, parse_json_reply
from .diff_summary import DiffSummary

VERDICTS = ("lgtm", "revise", "block", "unavailable")

_SYSTEM = """You are a read-only patch reviewer for an autonomous repo-maintenance agent.
You review the ACTUAL diff (not the plan). Judge: correctness, scope (does the
diff stay within the stated module?), risk, and whether verification is adequate.
Respond with JSON only:
{"verdict": "lgtm" | "revise" | "block", "critiques": ["...", ...]}
- lgtm: safe to proceed/push.
- revise: fixable issues; list concrete critiques.
- block: must not ship; a human should look.
Be strict when tests were not run or files outside scope changed."""


@dataclass
class ReviewVerdict:
    verdict: str
    critiques: list[str] = field(default_factory=list)
    raw: str = ""

    @property
    def passing(self) -> bool:
        return self.verdict == "lgtm"


_PLAN_SYSTEM = """You review an EXECUTION PLAN (playbook) an autonomous repo-maintenance
agent generated or adapted, BEFORE it runs. Judge: does the step sequence match the
stated task; are the steps safe for the task's tier (read-only tasks must contain no
write/push steps); is anything missing that would make results untrustworthy?
Respond with JSON only: {"verdict": "lgtm" | "revise" | "block", "critiques": ["..."]}"""


def run_plan_review(llm: LLM | None, *, playbook_doc: str, task: str,
                    model: str | None = None) -> ReviewVerdict:
    """Plan-Review gate for adapted/generated playbooks. Fail-closed like
    patch review: no reviewer -> `unavailable` (caller must gate on a human)."""
    if llm is None or not llm.available:
        return ReviewVerdict("unavailable", ["no reviewer LLM configured"])
    prompt = f"Task: {task}\n\nPlan:\n```yaml\n{playbook_doc[:20_000]}\n```"
    reply = llm.create(system=_PLAN_SYSTEM,
                       messages=[{"role": "user", "content": prompt}], model=model)
    obj = parse_json_reply(reply.text)
    if not obj or obj.get("verdict") not in ("lgtm", "revise", "block"):
        return ReviewVerdict("revise", ["reviewer reply unparseable"], reply.text)
    return ReviewVerdict(obj["verdict"], [str(c) for c in obj.get("critiques", [])],
                         reply.text)


def run_patch_review(
    llm: LLM | None,
    *,
    diff_text: str,
    summary: DiffSummary,
    fired_rules: list[str],
    context: str = "",
    model: str | None = None,
) -> ReviewVerdict:
    if llm is None or not llm.available:
        return ReviewVerdict("unavailable", ["no reviewer LLM configured"])

    prompt = (
        f"Trigger rules fired: {', '.join(fired_rules) or 'none'}\n"
        f"Changed files ({len(summary.changed_files)}): {summary.changed_files}\n"
        f"Diffstat: +{summary.insertions}/-{summary.deletions}\n"
        f"Out-of-scope files: {summary.out_of_scope_files}\n"
        f"Full-file rewrites: {summary.full_file_writes}\n"
        f"Tests run: {summary.tests_run or 'NONE'}\n"
        f"{context}\n\n--- DIFF ---\n{diff_text[:60_000]}"
    )
    reply = llm.create(system=_SYSTEM, messages=[{"role": "user", "content": prompt}],
                       model=model)
    obj = parse_json_reply(reply.text)
    if not obj or obj.get("verdict") not in ("lgtm", "revise", "block"):
        # unparseable review -> conservative
        return ReviewVerdict("revise", ["reviewer reply unparseable"], reply.text)
    return ReviewVerdict(obj["verdict"], [str(c) for c in obj.get("critiques", [])],
                         reply.text)
