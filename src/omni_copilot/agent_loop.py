"""Minimal tool-use agent loop, ToolScope-constrained and RunTrace-audited.

Agent Steps are the highest-risk step kind (design §3.X.7): the loop only ever
sees the tools its scope allows, and every call goes through tools.dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .llm import LLM, Reply
from .run_trace import RunTrace
from .scopes import ToolScope
from .tools import dispatch, tool_definitions_for


@dataclass
class AgentOutcome:
    text: str
    iterations: int
    tool_calls: int
    truncated: bool = False
    refusals: list[str] = field(default_factory=list)


def run_agent(
    llm: LLM,
    *,
    system: str,
    prompt: str,
    scope: ToolScope,
    trace: RunTrace | None = None,
    model: str | None = None,
    max_iters: int = 40,
) -> AgentOutcome:
    messages: list[dict] = [{"role": "user", "content": prompt}]
    tools = tool_definitions_for(scope)
    tool_calls = 0
    refusals: list[str] = []

    for i in range(1, max_iters + 1):
        reply: Reply = llm.create(system=system, messages=messages, tools=tools, model=model)
        assistant_content: list[dict] = []
        for b in reply.blocks:
            if b.type == "text":
                assistant_content.append({"type": "text", "text": b.text})
            else:
                assistant_content.append(
                    {"type": "tool_use", "id": b.id, "name": b.name, "input": b.input}
                )
        messages.append({"role": "assistant", "content": assistant_content})

        uses = reply.tool_uses
        if not uses:
            return AgentOutcome(reply.text, i, tool_calls, refusals=refusals)

        results = []
        for use in uses:
            tool_calls += 1
            out = dispatch(use.name, use.input, scope=scope, trace=trace)
            content = out.get("result") if out["ok"] else out.get("error", "error")
            if not out["ok"] and str(content).startswith("refused:"):
                refusals.append(str(content))
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": use.id,
                    "content": str(content),
                    "is_error": not out["ok"],
                }
            )
        messages.append({"role": "user", "content": results})

    return AgentOutcome("(agent hit max iterations)", max_iters, tool_calls, truncated=True,
                        refusals=refusals)
