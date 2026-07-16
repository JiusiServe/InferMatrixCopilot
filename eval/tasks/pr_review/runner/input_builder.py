"""Build the exact agent-visible input without leaking GT or review history."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ..benchmark.schema import BenchmarkItem, CommitInfo, LinkedIssue


class AgentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "pr-review-input-v0.1"
    benchmark_id: str
    repository: str
    pr_number: int
    title: str
    body: str
    base_branch: str
    base_sha: str
    head_sha: str
    commits: list[CommitInfo]
    changed_files: list[str]
    diff: str
    linked_issue: LinkedIssue | None = None


def build_agent_input(item: BenchmarkItem, *, diff: str) -> AgentInput:
    """Project a benchmark item onto the public contract; GT fields are impossible to include."""
    return AgentInput(
        benchmark_id=item.benchmark_id,
        repository=item.repository,
        pr_number=item.pr_number,
        title=item.title,
        body=item.body,
        base_branch=item.base_branch,
        base_sha=item.base_sha,
        head_sha=item.head_sha,
        commits=item.commits,
        changed_files=item.changed_files,
        diff=diff,
        linked_issue=item.linked_issue,
    )
