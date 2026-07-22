"""Versioned configuration for evaluated PR-review subjects and matrices."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SkillConfig(StrictModel):
    path: str
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    source_repository: str = ""
    source_ref: str = ""
    source_blob_sha: str = ""


class CopilotConfig(StrictModel):
    review_depth: Literal["auto", "light", "standard", "full"] = "auto"
    review_ensemble: bool = True
    profile_briefing_enabled: bool = True
    builtin_skills_enabled: bool = True
    review_max_iters: int = Field(default=12, ge=1, le=100)
    ensemble_lens_max_iters: int = Field(default=10, ge=1, le=100)
    ensemble_parallel: bool = True
    ensemble_stagger_seconds: float = Field(default=0.0, ge=0.0, le=60.0)


class AgentSubjectConfig(StrictModel):
    schema_version: Literal["pr-review-agent-config-v0.1"] = "pr-review-agent-config-v0.1"
    name: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    kind: Literal["copilot", "copilot_with_skill", "skill_only"]
    version: str = Field(min_length=1)
    model: str = ""
    model_family: str = ""
    prompt_version: str = "pr-review-output-v0.1"
    model_parameters: dict[str, Any] = Field(default_factory=dict)
    max_iters: int = Field(default=20, ge=1, le=100)
    copilot: CopilotConfig = Field(default_factory=CopilotConfig)
    skill: SkillConfig | None = None

    @model_validator(mode="after")
    def validate_kind(self) -> "AgentSubjectConfig":
        if self.kind in {"copilot_with_skill", "skill_only"} and self.skill is None:
            raise ValueError(f"{self.kind} requires skill configuration")
        if self.kind == "copilot" and self.skill is not None:
            raise ValueError("copilot baseline must not include an external skill")
        return self


class ExperimentMatrixConfig(StrictModel):
    schema_version: Literal["pr-review-experiment-matrix-v0.1"] = (
        "pr-review-experiment-matrix-v0.1"
    )
    name: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    agents: list[str] = Field(min_length=1)
    repetitions: int = Field(default=1, ge=1, le=20)


def _expand(value: Any) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, list):
        return [_expand(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand(item) for key, item in value.items()}
    return value


def _load_yaml(path: str | Path) -> tuple[Path, dict[str, Any]]:
    resolved = Path(path).expanduser().resolve()
    value = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"configuration must be a YAML mapping: {resolved}")
    return resolved, _expand(value)


def load_agent_config(path: str | Path) -> tuple[Path, AgentSubjectConfig]:
    resolved, value = _load_yaml(path)
    return resolved, AgentSubjectConfig.model_validate(value)


def load_experiment_matrix(path: str | Path) -> tuple[Path, ExperimentMatrixConfig]:
    resolved, value = _load_yaml(path)
    return resolved, ExperimentMatrixConfig.model_validate(value)


def resolve_relative(path: str, *, config_path: Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = config_path.parent / candidate
    return candidate.resolve()


def read_verified_skill(config: SkillConfig, *, config_path: Path) -> tuple[Path, str, str]:
    path = resolve_relative(config.path, config_path=config_path)
    text = path.read_text(encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if config.sha256 and digest != config.sha256:
        raise ValueError(
            f"skill SHA-256 mismatch for {path}: expected {config.sha256}, got {digest}"
        )
    return path, text, digest
