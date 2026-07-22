"""Minimal skill-only reviewer: model + one skill + evaluator-owned tools."""

from __future__ import annotations

from omni_copilot.agent_loop import run_agent
from omni_copilot.llm import LLM

from ..runner.input_builder import AgentInput
from ..runner.tools import StaticToolExecutor
from ..runner.trace_collector import TraceCollector
from .base import (
    MeteredLLM,
    output_contract_text,
    render_agent_input,
    static_tool_defs,
    static_tool_scope,
)
from .config import AgentSubjectConfig


class SkillOnlyAgentAdapter:
    def __init__(self, config: AgentSubjectConfig, *, skill_text: str, llm: LLM):
        self.config = config
        self.skill_text = skill_text
        self.llm = llm
        self.model = config.model or llm.settings.agent_model
        self.version = config.version

    def review(
        self,
        agent_input: AgentInput,
        *,
        workspace: str,
        tools: StaticToolExecutor,
        trace: TraceCollector,
    ) -> str:
        metered = MeteredLLM(self.llm, trace)
        system = (
            "You are the agent under test in an OFFLINE, static PR-review benchmark. "
            "Use only the provided read-only tools. Network, GitHub, code execution, "
            "test execution, posting, and repository mutation are unavailable and must "
            "not be attempted. The skill below is task guidance, but the benchmark "
            "constraints and output contract in this system message take precedence. "
            "Investigate claims before reporting them. Your final message must be exactly "
            "one JSON object matching the contract; emit no Markdown fence or extra prose.\n\n"
            "## Required output contract\n" + output_contract_text()
        )
        prompt = (
            "## Skill under evaluation\n<skill>\n"
            + self.skill_text
            + "\n</skill>\n\n"
            + render_agent_input(agent_input)
        )
        outcome = run_agent(
            metered,
            system=system,
            prompt=prompt,
            scope=static_tool_scope(),
            trace=None,
            model=self.config.model or None,
            max_iters=self.config.max_iters,
            extra_tools=static_tool_defs(tools),
        )
        trace.record(
            "subject_result",
            subject_kind=self.config.kind,
            iterations=outcome.iterations,
            tool_calls=outcome.tool_calls,
            truncated=outcome.truncated,
        )
        return outcome.text
