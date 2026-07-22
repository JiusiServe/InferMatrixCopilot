"""TaskSpec — the structured product of intent parsing (design §3.Y.2).

The tier is derived from the task kind, never from user text: natural language
can never widen permissions (§3.Y.4).
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

TaskKind = Literal[
    "repo_rebase", "pr_rebase", "pr_debug", "pr_review", "issue_answer", "issue_filter",
    "repo_profile",
]

READ_ONLY_KINDS: frozenset[str] = frozenset({"pr_review", "issue_answer", "issue_filter"})

# blast-radius tier per kind (design §3.2): L0 reuse-locked, L1 adapt-vetted, L2 generate
KIND_TIER: dict[str, str] = {
    "repo_rebase": "L0",
    "pr_rebase": "L1",
    "pr_debug": "L1",
    "pr_review": "L2",
    "issue_answer": "L2",
    "issue_filter": "L2",
    # profile establishment reads the target repo but writes knowledge
    # (adapters/<repo>/) — confirm-gated like other write-capable kinds
    "repo_profile": "L2",
}


class TaskSpec(BaseModel):
    """The structured, validated task the whole pipeline runs on: a `kind`
    plus its target (`repo`, optional `pr`/`issue`) and the write-intent flags
    (`report_only`, `post`, `params`). The blast-radius tier is derived from
    `kind` alone — user text can never widen permissions.

    `mode` is the dual-path (双路径) execution tier, set from intent and shared
    by the whole run: `eco` (cost-effective model, the default) or `performance`
    (high-capability model, only when the user explicitly asks for it). It
    selects the agent-reasoning model per run; it is orthogonal to `tier` (which
    still governs blast radius / permissions — a cheaper model never widens
    what a task may do)."""

    kind: TaskKind
    mode: Literal["eco", "performance"] = "eco"
    repo: str = "vllm-omni"
    pr: Optional[int] = None
    issue: Optional[int] = None
    report_only: bool = False
    post: bool = False  # outward writes (PR comments / issue replies) — explicit only
    params: dict = Field(default_factory=dict)

    @property
    def tier(self) -> str:
        """The blast-radius tier (L0/L1/L2) fixed by this task's kind."""
        return KIND_TIER[self.kind]

    @property
    def read_only(self) -> bool:
        """Whether this run makes no writes: inherently-read kinds are read-only
        unless `post` publishes outward; other kinds are read-only only when
        `report_only` is set."""
        if self.kind in READ_ONLY_KINDS:
            return not self.post
        return self.report_only

    @property
    def confirm_required(self) -> bool:
        """Write/push-capable tasks must be confirmed by the user (§3.Y.4)."""
        return not self.read_only

    def describe(self) -> str:
        """One-line human summary: kind, target PR/issue, repo, tier, and any
        report-only/post flags — used in plan printouts and traces."""
        target = ""
        if self.pr:
            target = f" PR #{self.pr}"
        if self.issue:
            target = f" issue #{self.issue}"
        flags = []
        if self.mode == "performance":
            flags.append("performance")  # eco is the default, kept implicit
        if self.report_only:
            flags.append("report-only")
        if self.post:
            flags.append("post")
        suffix = f" [{', '.join(flags)}]" if flags else ""
        return f"{self.kind}{target} on {self.repo} (tier {self.tier}){suffix}"
