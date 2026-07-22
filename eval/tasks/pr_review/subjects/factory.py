"""Build concrete evaluated-agent adapters from versioned YAML configs."""

from __future__ import annotations

from pathlib import Path

from omni_copilot.config import Settings
from omni_copilot.llm import LLM

from .config import AgentSubjectConfig, load_agent_config, read_verified_skill
from .copilot_adapter import CopilotAgentAdapter
from .skill_adapter import SkillOnlyAgentAdapter


def build_agent_adapter(
    config: AgentSubjectConfig,
    *,
    config_path: Path,
    llm: LLM | None = None,
):
    skill_text = ""
    skill_digest = ""
    if config.skill is not None:
        _, skill_text, skill_digest = read_verified_skill(config.skill, config_path=config_path)

    provider = llm
    if provider is None:
        settings = Settings(
            agent_model=config.model or "claude-sonnet-5",
            eco_model=config.model,
            performance_model=config.model,
            reviewer_model=config.model,
        )
        provider = LLM(settings)

    if config.kind == "skill_only":
        adapter = SkillOnlyAgentAdapter(config, skill_text=skill_text, llm=provider)
    elif config.kind in {"copilot", "copilot_with_skill"}:
        adapter = CopilotAgentAdapter(
            config,
            external_skill_text=skill_text if config.kind == "copilot_with_skill" else "",
            llm=provider,
        )
    else:  # pragma: no cover - pydantic already rejects this
        raise ValueError(f"unsupported subject kind: {config.kind}")

    if skill_digest:
        adapter.version = f"{adapter.version}+skill.{skill_digest[:12]}"
    return adapter


def load_and_build_agent_adapter(path: str | Path, *, llm: LLM | None = None):
    config_path, config = load_agent_config(path)
    return config, build_agent_adapter(config, config_path=config_path, llm=llm)
