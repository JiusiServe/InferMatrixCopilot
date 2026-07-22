"""Common subject abstractions and adapters shared by all experiment arms."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Protocol

from omni_copilot.llm import LLM, Reply
from omni_copilot.scopes import ToolScope
from omni_copilot.tools import ToolDef

from ..benchmark.schema import Category, Severity, Verdict
from ..runner.input_builder import AgentInput
from ..runner.output_schema import AgentReview
from ..runner.tools import StaticToolExecutor
from ..runner.trace_collector import TraceCollector


class EvaluatedReviewSubject(Protocol):
    version: str

    def review(
        self,
        agent_input: AgentInput,
        *,
        workspace: str,
        tools: StaticToolExecutor,
        trace: TraceCollector,
    ) -> str:
        ...


class MeteredLLM:
    """Count every provider call, including planner/reducer/repair calls."""

    def __init__(self, inner: LLM, trace: TraceCollector):
        self.inner = inner
        self.trace = trace

    @property
    def available(self) -> bool:
        return self.inner.available

    def create(self, **kwargs: Any) -> Reply:
        reply = self.inner.create(**kwargs)
        usage = reply.usage or {}
        self.trace.record(
            "model_usage",
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            cached_tokens=int(usage.get("cache_read_input_tokens", 0)),
            model=str(kwargs.get("model") or ""),
        )
        return reply


class TraceBridge:
    """Forward copilot trace events without double-counting static tool calls."""

    def __init__(self, trace: TraceCollector):
        self.trace = trace

    def record(self, kind: str, **fields: Any) -> None:
        if kind in {"tool_call", "tool_refused"}:
            return
        self.trace.record(f"copilot_{kind}", **fields)


def static_tool_defs(executor: StaticToolExecutor) -> dict[str, ToolDef]:
    """Expose evaluator-owned read-only tools through the copilot tool loop."""

    def read_file(path: str, offset: int = 0, max_bytes: int = 48_000, **_: Any) -> str:
        text = executor.read_file(path)
        window = text[offset : offset + max_bytes]
        if offset + max_bytes < len(text):
            window += (
                f"\n...[truncated at char {offset + max_bytes} of {len(text)}; "
                f"call read_file with offset={offset + max_bytes}]"
            )
        return window

    def list_dir(path: str = ".", **_: Any) -> str:
        return "\n".join(executor.list_directory(path))

    def grep(pattern: str, path: str = ".", regex: bool = False, **_: Any) -> str:
        rows = executor.search_text(pattern, path=path, regex=regex)
        return "\n".join(
            f"{row['file']}:{row['line']}:{row['text']}" for row in rows
        ) or "(no matches)"

    def git_readonly(args: list[str], **_: Any) -> str:
        return executor.git(*(str(arg) for arg in args))

    string = {"type": "string"}
    return {
        "read_file": ToolDef(
            "read_file",
            "Read a repository text file in bounded windows.",
            {
                "type": "object",
                "properties": {"path": string, "offset": {"type": "integer"}},
                "required": ["path"],
            },
            read_file,
        ),
        "list_dir": ToolDef(
            "list_dir",
            "List a repository directory.",
            {"type": "object", "properties": {"path": string}, "required": ["path"]},
            list_dir,
        ),
        "grep": ToolDef(
            "grep",
            "Search repository text and return file:line:text rows.",
            {
                "type": "object",
                "properties": {
                    "pattern": string,
                    "path": string,
                    "regex": {"type": "boolean"},
                },
                "required": ["pattern", "path"],
            },
            grep,
        ),
        "git_readonly": ToolDef(
            "git_readonly",
            "Run an allowlisted read-only git subcommand using an argv array.",
            {
                "type": "object",
                "properties": {
                    "args": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["args"],
            },
            git_readonly,
        ),
    }


def static_tool_scope() -> ToolScope:
    # All tools are evaluator-vetted `extra_tools`; no product builtin tool is exposed.
    return ToolScope(name="pr_review_eval", allowed_tools=frozenset(), read_only=True)


_CATEGORY_ALIASES: dict[str, Category] = {
    "correctness": Category.CORRECTNESS,
    "compatibility": Category.COMPATIBILITY_API,
    "compatibility_api": Category.COMPATIBILITY_API,
    "api": Category.COMPATIBILITY_API,
    "concurrency": Category.CONCURRENCY,
    "performance": Category.PERFORMANCE_RESOURCE,
    "performance_resource": Category.PERFORMANCE_RESOURCE,
    "resource": Category.PERFORMANCE_RESOURCE,
    "security": Category.SECURITY_SAFETY,
    "safety": Category.SECURITY_SAFETY,
    "security_safety": Category.SECURITY_SAFETY,
    "test": Category.TEST,
    "tests": Category.TEST,
    "documentation": Category.DOCUMENTATION,
    "docs": Category.DOCUMENTATION,
    "maintainability": Category.MAINTAINABILITY,
}


def normalize_category(value: Any, text: str = "") -> Category:
    key = str(value or "").strip().lower().replace("-", "_").replace("/", "_")
    if key in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[key]
    hay = text.lower()
    if any(token in hay for token in ("test", "pytest", "coverage", "benchmark")):
        return Category.TEST
    if any(token in hay for token in ("docstring", "documentation", "readme", "docs/")):
        return Category.DOCUMENTATION
    if any(token in hay for token in ("api", "compat", "default", "protocol", "schema")):
        return Category.COMPATIBILITY_API
    if any(token in hay for token in ("race", "deadlock", "async", "concurrent")):
        return Category.CONCURRENCY
    if any(token in hay for token in ("memory", "latency", "performance", "throughput")):
        return Category.PERFORMANCE_RESOURCE
    if any(token in hay for token in ("security", "unsafe", "injection", "secret")):
        return Category.SECURITY_SAFETY
    return Category.CORRECTNESS


def normalize_severity(value: Any) -> Severity:
    key = str(value or "minor").strip().lower()
    mapping = {
        "critical": Severity.CRITICAL,
        "blocker": Severity.BLOCKER,
        "major": Severity.MAJOR,
        "minor": Severity.MINOR,
        "nit": Severity.NIT,
    }
    return mapping.get(key, Severity.MINOR)


def _evidence_from_comment(comment: dict[str, Any], file: str, line: int) -> list[dict[str, Any]]:
    reason = str(comment.get("evidence") or "Finding is grounded at the reported repository location.")
    locations: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for match in re.finditer(r"(?P<file>[A-Za-z0-9_./-]+\.[A-Za-z0-9_+-]+):(?P<line>\d+)", reason):
        key = (match.group("file"), int(match.group("line")))
        if key in seen:
            continue
        seen.add(key)
        locations.append(
            {
                "file": key[0],
                "start_line": key[1],
                "end_line": key[1],
                "reason": reason,
            }
        )
    if not locations:
        locations.append(
            {
                "file": file,
                "start_line": line,
                "end_line": line,
                "reason": reason,
            }
        )
    return locations[:5]


def copilot_output_to_review(output: dict[str, Any], *, summary: str = "") -> AgentReview:
    comments = output.get("review_comments") or []
    findings: list[dict[str, Any]] = []
    blocking = False
    for index, raw in enumerate(comments, start=1):
        if not isinstance(raw, dict):
            continue
        file = str(raw.get("file") or "").strip()
        try:
            line = max(1, int(raw.get("line") or 1))
        except (TypeError, ValueError):
            line = 1
        severity = normalize_severity(raw.get("severity"))
        description = str(raw.get("comment") or raw.get("description") or "").strip()
        uncertainty_text = (description + " " + str(raw.get("evidence") or "")).lower()
        uncertain = any(
            marker in uncertainty_text
            for marker in (
                "uncertain",
                "unverified",
                "could not verify",
                "cannot verify",
                "budget exhaust",
                "not able to confirm",
            )
        )
        if severity in {Severity.CRITICAL, Severity.BLOCKER, Severity.MAJOR} and not uncertain:
            blocking = True
        if not file or not description:
            continue
        title = description.splitlines()[0].strip()
        if len(title) > 120:
            title = title[:117].rstrip() + "..."
        findings.append(
            {
                "id": f"finding-{index}",
                "title": title,
                "description": description,
                "severity": severity,
                "category": normalize_category(raw.get("category"), description),
                "location": {"file": file, "start_line": line, "end_line": line},
                "evidence": _evidence_from_comment(raw, file, line),
            }
        )
    review_summary = str(output.get("summary") or summary or "Review completed.").strip()
    return AgentReview.model_validate(
        {
            "verdict": Verdict.REQUEST_CHANGES if blocking else Verdict.APPROVE,
            "summary": review_summary,
            "findings": findings,
        }
    )


def render_agent_input(agent_input: AgentInput) -> str:
    linked = ""
    if agent_input.linked_issue is not None:
        linked = (
            f"\n## Linked issue #{agent_input.linked_issue.number}\n"
            f"{agent_input.linked_issue.title}\n{agent_input.linked_issue.body}\n"
        )
    commits = "\n".join(f"- {item.sha}: {item.message}" for item in agent_input.commits)
    return (
        f"# Offline PR review\n"
        f"Repository: {agent_input.repository}\n"
        f"PR: #{agent_input.pr_number}\n"
        f"Title: {agent_input.title}\n"
        f"Base: {agent_input.base_branch} ({agent_input.base_sha})\n"
        f"Head: {agent_input.head_sha}\n\n"
        f"## PR body\n{agent_input.body}\n{linked}\n"
        f"## Commits\n{commits or '(none supplied)'}\n\n"
        f"## Changed files\n" + "\n".join(f"- {path}" for path in agent_input.changed_files) +
        f"\n\n## Frozen diff\n```diff\n{agent_input.diff}\n```"
    )


def output_contract_text() -> str:
    return json.dumps(
        {
            "schema_version": "pr-review-output-v0.1",
            "verdict": "APPROVE | REQUEST_CHANGES",
            "summary": "non-empty string",
            "findings": [
                {
                    "id": "unique string",
                    "title": "short title",
                    "description": "actionable explanation",
                    "severity": "Critical | Blocker | Major | Minor | Nit",
                    "category": (
                        "correctness | compatibility_api | concurrency | "
                        "performance_resource | security_safety | test | "
                        "documentation | maintainability"
                    ),
                    "location": {
                        "file": "repository-relative path",
                        "start_line": 1,
                        "end_line": 1,
                    },
                    "evidence": [
                        {
                            "file": "repository-relative path",
                            "start_line": 1,
                            "end_line": 1,
                            "reason": "what was checked",
                        }
                    ],
                }
            ],
        },
        ensure_ascii=False,
        indent=2,
    )
