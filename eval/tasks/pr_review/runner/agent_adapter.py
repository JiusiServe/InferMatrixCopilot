"""Adapter boundary between the evaluator and any PR-review implementation."""

from __future__ import annotations

from typing import Protocol

from .input_builder import AgentInput
from .tools import StaticToolExecutor
from .trace_collector import TraceCollector


class AgentAdapter(Protocol):
    version: str

    def review(
        self, agent_input: AgentInput, *, workspace: str, tools: StaticToolExecutor, trace: TraceCollector
    ) -> str:
        """Return the raw structured-output text produced by the evaluated agent."""


class CallableAgentAdapter:
    """Small adapter useful for local integrations and deterministic tests."""

    def __init__(self, callback, *, version: str = "callable-v1"):
        self.callback = callback
        self.version = version

    def review(
        self, agent_input: AgentInput, *, workspace: str, tools: StaticToolExecutor, trace: TraceCollector
    ) -> str:
        return str(self.callback(agent_input=agent_input, workspace=workspace, tools=tools, trace=trace))
