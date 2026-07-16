"""Versioned benchmark contracts for offline PR-review evaluation."""

from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    """Base model that rejects undocumented fields."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Severity(StrEnum):
    CRITICAL = "Critical"
    BLOCKER = "Blocker"
    MAJOR = "Major"
    MINOR = "Minor"
    NIT = "Nit"


SEVERITY_WEIGHT: dict[Severity, float] = {
    Severity.CRITICAL: 4.0,
    Severity.BLOCKER: 3.0,
    Severity.MAJOR: 2.0,
    Severity.MINOR: 1.0,
    Severity.NIT: 0.5,
}

SEVERITY_VALUE: dict[Severity, int] = {
    Severity.CRITICAL: 4,
    Severity.BLOCKER: 3,
    Severity.MAJOR: 2,
    Severity.MINOR: 1,
    Severity.NIT: 0,
}


class Category(StrEnum):
    CORRECTNESS = "correctness"
    COMPATIBILITY_API = "compatibility_api"
    CONCURRENCY = "concurrency"
    PERFORMANCE_RESOURCE = "performance_resource"
    SECURITY_SAFETY = "security_safety"
    TEST = "test"
    DOCUMENTATION = "documentation"
    MAINTAINABILITY = "maintainability"


class Verdict(StrEnum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"


class CleanStatus(StrEnum):
    BUGGY = "buggy"
    AUTO_CERTIFIED_CLEAN = "auto_certified_clean"


class BenchmarkSplit(StrEnum):
    DEV = "dev"
    TEST = "test"


class SourceLocation(StrictModel):
    file: str = Field(min_length=1)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    symbol: str | None = None

    @model_validator(mode="after")
    def validate_location(self) -> "SourceLocation":
        if self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line")
        path = PurePosixPath(self.file)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("file must be a repository-relative POSIX path")
        return self


class EvidenceLocation(SourceLocation):
    reason: str | None = None


class CommitInfo(StrictModel):
    sha: str = Field(min_length=7)
    message: str = ""


class LinkedIssue(StrictModel):
    number: int = Field(gt=0)
    title: str
    body: str = ""


class GroundTruthFinding(StrictModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_.:-]+$")
    summary: str = Field(min_length=1)
    description: str = Field(min_length=1)
    severity: Severity
    category: Category
    merge_blocking: bool
    location_required: bool = True
    accepted_locations: list[SourceLocation] = Field(default_factory=list)
    evidence: list[EvidenceLocation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_semantics(self) -> "GroundTruthFinding":
        if self.severity in {Severity.CRITICAL, Severity.BLOCKER} and not self.merge_blocking:
            raise ValueError(f"{self.severity.value} findings must be merge-blocking")
        if self.severity in {Severity.MINOR, Severity.NIT} and self.merge_blocking:
            raise ValueError(f"{self.severity.value} findings must be non-blocking")
        if self.location_required and not self.accepted_locations:
            raise ValueError("location_required findings need accepted_locations")
        return self


class BenchmarkItem(StrictModel):
    schema_version: Literal["pr-review-item-v0.1"] = "pr-review-item-v0.1"
    benchmark_id: str = Field(min_length=1)
    repository: str = Field(pattern=r"^[^/\s]+/[^/\s]+$")
    pr_number: int = Field(gt=0)
    base_branch: str = "main"
    base_sha: str = Field(min_length=7)
    head_sha: str = Field(min_length=7)
    title: str
    body: str = ""
    commits: list[CommitInfo] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    linked_issue: LinkedIssue | None = None
    expected_verdict: Verdict
    clean_status: CleanStatus
    split: BenchmarkSplit = BenchmarkSplit.TEST
    gt_findings: list[GroundTruthFinding] = Field(default_factory=list)
    invalidated: bool = False
    invalidation_reason: str | None = None

    @model_validator(mode="after")
    def validate_item(self) -> "BenchmarkItem":
        if self.base_sha == self.head_sha:
            raise ValueError("base_sha and head_sha must differ")
        if len(set(self.changed_files)) != len(self.changed_files):
            raise ValueError("changed_files contains duplicates")
        ids = [finding.id for finding in self.gt_findings]
        if len(ids) != len(set(ids)):
            raise ValueError("GT finding IDs must be unique within a PR")

        derived = (
            Verdict.REQUEST_CHANGES
            if any(f.merge_blocking for f in self.gt_findings)
            else Verdict.APPROVE
        )
        if self.expected_verdict != derived:
            raise ValueError(
                f"expected_verdict must be derived from merge_blocking GT findings: {derived.value}"
            )
        if self.clean_status == CleanStatus.AUTO_CERTIFIED_CLEAN and self.gt_findings:
            raise ValueError("auto-certified clean PRs cannot contain GT findings")
        if self.clean_status == CleanStatus.BUGGY and not self.gt_findings:
            raise ValueError("buggy PRs must contain at least one GT finding")
        if self.invalidated and not self.invalidation_reason:
            raise ValueError("invalidated benchmark items require invalidation_reason")
        return self


class BenchmarkManifestEntry(StrictModel):
    benchmark_id: str
    item: str
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class BenchmarkManifest(StrictModel):
    schema_version: Literal["pr-review-manifest-v0.1"] = "pr-review-manifest-v0.1"
    benchmark_version: str = Field(min_length=1)
    rubric_version: str = Field(min_length=1)
    judge_version: str = Field(min_length=1)
    created_at: str
    entries: list[BenchmarkManifestEntry]

    @model_validator(mode="after")
    def validate_entries(self) -> "BenchmarkManifest":
        ids = [entry.benchmark_id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("manifest benchmark IDs must be unique")
        paths = [entry.item for entry in self.entries]
        if len(paths) != len(set(paths)):
            raise ValueError("manifest item paths must be unique")
        return self


NonEmptyStr = Annotated[str, Field(min_length=1)]
