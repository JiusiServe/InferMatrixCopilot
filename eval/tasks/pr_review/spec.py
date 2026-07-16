"""Load the audit-friendly, versioned evaluation specification."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .benchmark.schema import Category, SEVERITY_VALUE, SEVERITY_WEIGHT, Severity, Verdict


class SeverityRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weight: float
    value: int
    merge_blocking: str


class JuryRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    standard_judges: int
    positions_per_judge: int
    first_round_required_votes: int
    duplicate_required_votes: int
    cumulative_round2_required_votes: int
    standard_total_votes: int
    cumulative_total_votes: int


class CandidateMatcherRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    threshold: float
    max_candidates_per_prediction: int


class EvaluationSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str
    benchmark_item_schema: str
    agent_input_schema: str
    agent_output_schema: str
    rubric_version: str
    judge_version: str
    tool_policy_version: str
    max_findings: int = Field(gt=0)
    severity: dict[str, SeverityRule]
    categories: list[str]
    verdicts: list[str]
    adjudication_statuses: list[str]
    jury: JuryRule
    candidate_matcher: CandidateMatcherRule
    formal_match_threshold: float
    adjudication_coverage_threshold: float
    aggregation: dict[str, str]
    allowed_git_subcommands: list[str]

    @model_validator(mode="after")
    def consistent_with_contracts(self) -> "EvaluationSpec":
        if set(self.severity) != {value.value for value in Severity}:
            raise ValueError("severity rubric is inconsistent with Severity enum")
        for severity in Severity:
            rule = self.severity[severity.value]
            if rule.weight != SEVERITY_WEIGHT[severity] or rule.value != SEVERITY_VALUE[severity]:
                raise ValueError(f"severity constants disagree for {severity.value}")
        if set(self.categories) != {value.value for value in Category}:
            raise ValueError("category rubric is inconsistent with Category enum")
        if set(self.verdicts) != {value.value for value in Verdict}:
            raise ValueError("verdict rubric is inconsistent with Verdict enum")
        if self.jury.standard_judges * self.jury.positions_per_judge != self.jury.standard_total_votes:
            raise ValueError("jury total vote configuration is inconsistent")
        return self


def default_spec_path() -> Path:
    return Path(__file__).with_name("rubrics") / "pr-review-v0.1.yaml"


def load_evaluation_spec(path: str | Path | None = None) -> EvaluationSpec:
    target = Path(path) if path else default_spec_path()
    return EvaluationSpec.model_validate(yaml.safe_load(target.read_text(encoding="utf-8")))
