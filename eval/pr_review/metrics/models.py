"""Metric result models and evaluation input bundles."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..adjudication.models import AdjudicationRow
from ..benchmark.schema import BenchmarkItem
from ..runner.output_schema import AgentReview
from ..runner.trace_collector import RunMetadata


class PRResultInput(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    item: BenchmarkItem
    review: AgentReview | None = None
    adjudications: list[AdjudicationRow] = Field(default_factory=list)
    run_metadata: RunMetadata | None = None


class PerPRMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    benchmark_id: str
    included: bool = True
    exclusion_reason: str | None = None
    raw_recall: float | None = None
    weighted_recall: float | None = None
    valid_precision: float | None = None
    verdict_correct: bool = False
    false_approve: bool = False
    false_reject: bool = False
    merge_blocking_miss_rate: float | None = None
    finding_count: int = 0
    empty_review: bool = False
    duplicate_rate: float | None = None
    localization_accuracy: float | None = None
    severity_mae: float | None = None
    category_recall: dict[str, float] = Field(default_factory=dict)
    blocker_inflation_rate: float | None = None
    nit_rate: float | None = None
    adjudication_coverage: float = 1.0
    unverifiable_count: int = 0
    output_contract_failure: bool = False
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    total_tokens: int = 0
    wall_time_ms: int = 0
    tool_calls: int = 0
    policy_violation_count: int = 0


class Distribution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mean: float
    median: float
    p90: float
    maximum: float


class SummaryMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    benchmark_version: str
    rubric_version: str | None = None
    judge_version: str | None = None
    run_count: int
    included_pr_count: int
    buggy_pr_count: int
    clean_pr_count: int
    raw_recall_macro: float | None = None
    raw_recall_micro: float | None = None
    weighted_recall_macro: float | None = None
    weighted_recall_micro: float | None = None
    valid_finding_precision: float | None = None
    verdict_accuracy: float | None = None
    false_approve_rate: float | None = None
    false_reject_rate: float | None = None
    merge_blocking_miss_rate: float | None = None
    findings_per_pr: Distribution | None = None
    clean_pr_false_positive_rate: float | None = None
    buggy_pr_empty_rate: float | None = None
    duplicate_rate: float | None = None
    policy_violation_count: int = 0
    policy_violation_run_rate: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    total_tokens: int = 0
    wall_time_ms: int = 0
    tool_calls: int = 0
    localization_accuracy: float | None = None
    severity_mae: float | None = None
    category_recall: dict[str, float] = Field(default_factory=dict)
    category_macro_recall: float | None = None
    blocker_inflation_rate: float | None = None
    nit_rate: float | None = None
    adjudication_coverage: float = 1.0
    provisional: bool = False
    unverifiable_finding_count: int = 0
    benchmark_invalidated_pr_count: int = 0
    judge_round2_rate: float | None = None
    output_contract_failure_count: int = 0
