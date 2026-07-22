"""Unified Agent-Step runtime (Agent Step 修正方案 P0).

Every `StepSpec.kind == "agent"` step executes through `run_agent_step`, which
provides what the design promised and ad-hoc `ctx.llm.create()` calls did not:
a structured dispatch context, a capped+archived evidence pack, skill/memory
retrieval with read-only search tools, enforced ToolScope/PathScope, a
structured output contract with one repair round, and full RunTrace coverage.
`run_agent_step_ensemble` is the perspective-diverse robustness wrapper.

This was one 685-line module; it is now a package (dispatch/knowledge/utils are
the substrate; runner/ensemble the two entry points). The public surface below
is preserved so existing `from ..agent_runtime import X` importers are unchanged.
"""

from __future__ import annotations

from .dispatch import BASE_OUTPUT_SCHEMA, AgentDispatchContext
from .ensemble import run_agent_step_ensemble
from .knowledge import _resolve_adapter, _retrieve_skills
from .runner import run_agent_step

__all__ = [
    "AgentDispatchContext",
    "BASE_OUTPUT_SCHEMA",
    "run_agent_step",
    "run_agent_step_ensemble",
    "_resolve_adapter",
    "_retrieve_skills",
]
