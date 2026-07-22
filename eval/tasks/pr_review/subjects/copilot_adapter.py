"""Adapter that evaluates the copilot's real `agent.review_diff` step."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from omni_copilot.config import Settings
from omni_copilot.engine.step import StepContext
from omni_copilot.engine.steps.review.steps import _review_diff
from omni_copilot.llm import LLM

from ..runner.input_builder import AgentInput
from ..runner.tools import StaticToolExecutor
from ..runner.trace_collector import TraceCollector
from .base import (
    MeteredLLM,
    TraceBridge,
    copilot_output_to_review,
    static_tool_defs,
    static_tool_scope,
)
from .config import AgentSubjectConfig, PROJECT_ROOT


class CopilotAgentAdapter:
    def __init__(
        self,
        config: AgentSubjectConfig,
        *,
        external_skill_text: str = "",
        llm: LLM | None = None,
    ):
        self.config = config
        self.external_skill_text = external_skill_text
        self.settings = self._build_settings(config)
        self.llm = llm or LLM(self.settings)
        self.model = config.model or self.settings.agent_model
        self.version = config.version

    @staticmethod
    def _build_settings(config: AgentSubjectConfig) -> Settings:
        c = config.copilot
        skill_dir = PROJECT_ROOT / "skills" if c.builtin_skills_enabled else PROJECT_ROOT / "eval" / "resources" / "empty-skills"
        skill_dir.mkdir(parents=True, exist_ok=True)
        values = {
            "agent_model": config.model or "claude-sonnet-5",
            "eco_model": config.model,
            "performance_model": config.model,
            "reviewer_model": config.model,
            "review_depth": c.review_depth,
            "review_ensemble": c.review_ensemble,
            "profile_briefing_enabled": c.profile_briefing_enabled,
            "review_max_iters": c.review_max_iters,
            "ensemble_lens_max_iters": c.ensemble_lens_max_iters,
            "ensemble_parallel": c.ensemble_parallel,
            "ensemble_stagger_seconds": c.ensemble_stagger_seconds,
            "skills_dir": skill_dir,
            "allow_post": False,
            "allow_push": False,
        }
        return Settings(**values)

    def review(
        self,
        agent_input: AgentInput,
        *,
        workspace: str,
        tools: StaticToolExecutor,
        trace: TraceCollector,
    ) -> str:
        metered = MeteredLLM(self.llm, trace)
        run_dir = Path(workspace).parent / f"copilot-{self.config.name}"
        run_dir.mkdir(parents=True, exist_ok=True)
        guidance = ""
        if self.external_skill_text:
            guidance = (
                "\n\n## Explicit external review skill (experiment treatment)\n"
                "Treat this as additional review guidance. Offline benchmark constraints "
                "override any instruction to fetch from GitHub, execute tests, use hardware, "
                "or post comments.\n<external_skill>\n"
                + self.external_skill_text
                + "\n</external_skill>"
            )
        state = {
            "task_spec": {
                "kind": "pr_review",
                "pr": agent_input.pr_number,
                "repo": agent_input.repository.split("/", 1)[-1],
                "mode": "eco",
                "report_only": True,
                "post": False,
                "params": {"review_depth": self.config.copilot.review_depth},
            },
            "repo_path": workspace,
            "diff_text": agent_input.diff,
            "primary_files": list(agent_input.changed_files),
            "checkout_note": (
                f"offline fixed snapshot {agent_input.head_sha}; base {agent_input.base_sha}"
            ),
            "gate_report": (
                "Offline benchmark: live mergeability and CI are intentionally unavailable. "
                "Do not use network or execute tests."
            ),
            "protected_branches": [agent_input.base_branch],
            "review_extra_guidance": guidance,
            "review_extra_tools": static_tool_defs(tools),
            "review_tool_scope": static_tool_scope(),
        }
        ctx = StepContext(
            settings=self.settings,
            state=state,
            params={},
            run_dir=run_dir,
            trace=TraceBridge(trace),
            llm=metered,
        )
        result = asyncio.run(_review_diff(ctx))
        output = dict(result.outputs or {})
        if not result.ok and not output.get("review_comments"):
            raise RuntimeError(result.summary or "copilot review step failed")
        review = copilot_output_to_review(output, summary=result.summary)
        trace.record(
            "subject_result",
            subject_kind=self.config.kind,
            copilot_step_ok=result.ok,
            findings=len(review.findings),
        )
        return json.dumps(review.model_dump(mode="json"), ensure_ascii=False)
