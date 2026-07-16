"""Structured adjudication records consumed by deterministic metrics."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..benchmark.schema import Category, Severity


class FinalStatus(StrEnum):
    MATCHED_GT = "MATCHED_GT"
    VALID_PARTIAL = "VALID_PARTIAL"
    VALID_NEW = "VALID_NEW"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    DUPLICATE = "DUPLICATE"
    UNVERIFIABLE = "UNVERIFIABLE"


class MatchDecision(StrEnum):
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    PARTIAL = "PARTIAL"


class ValidityDecision(StrEnum):
    VALID_NEW = "VALID_NEW"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class DuplicateDecision(StrEnum):
    DUPLICATE = "DUPLICATE"
    DISTINCT = "DISTINCT"


class JudgeVote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    judge_id: str
    model_family: str
    position: str
    decision: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    evidence: list[str] = Field(default_factory=list)
    severity: Severity | None = None
    category: Category | None = None
    location_correct: bool | None = None
    merge_blocking: bool | None = None


class AdjudicationRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    benchmark_id: str
    prediction_id: str
    gt_id: str | None = None
    final_status: FinalStatus
    match_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    validity_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    judge_round: int = Field(default=1, ge=0, le=2)
    judge_votes: list[JudgeVote] = Field(default_factory=list)
    predicted_severity: Severity
    ground_truth_severity: Severity | None = None
    jury_severity: Severity | None = None
    predicted_category: Category
    ground_truth_category: Category | None = None
    location_correct: bool | None = None
    merge_blocking: bool | None = None
    duplicate_of: str | None = None
    unverifiable_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_status(self) -> "AdjudicationRow":
        if self.final_status == FinalStatus.MATCHED_GT and not self.gt_id:
            raise ValueError("MATCHED_GT rows require gt_id")
        if self.final_status == FinalStatus.MATCHED_GT and self.ground_truth_severity is None:
            raise ValueError("MATCHED_GT rows require ground_truth_severity")
        if self.final_status == FinalStatus.DUPLICATE and not self.duplicate_of:
            raise ValueError("DUPLICATE rows require duplicate_of")
        if self.final_status == FinalStatus.UNVERIFIABLE and not self.unverifiable_reason:
            raise ValueError("UNVERIFIABLE rows require unverifiable_reason")
        return self

    @property
    def effective_true_severity(self) -> Severity | None:
        if self.final_status == FinalStatus.MATCHED_GT:
            return self.ground_truth_severity
        return self.jury_severity
