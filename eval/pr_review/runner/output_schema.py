"""Strict output contract for the evaluated PR-review agent."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ..benchmark.schema import Category, EvidenceLocation, Severity, SourceLocation, Verdict
from .format_repair import repair_json_text

MAX_FINDINGS = 20


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FindingLocation(SourceLocation):
    pass


class FindingEvidence(EvidenceLocation):
    reason: str = Field(min_length=1)


class AgentFinding(StrictModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    severity: Severity
    category: Category
    location: FindingLocation
    evidence: list[FindingEvidence] = Field(min_length=1)


class AgentReview(StrictModel):
    schema_version: Literal["pr-review-output-v0.1"] = "pr-review-output-v0.1"
    verdict: Verdict
    summary: str = Field(min_length=1)
    findings: list[AgentFinding] = Field(default_factory=list, max_length=MAX_FINDINGS)

    @model_validator(mode="after")
    def unique_finding_ids(self) -> "AgentReview":
        ids = [finding.id for finding in self.findings]
        if len(ids) != len(set(ids)):
            raise ValueError("finding IDs must be unique")
        return self


class OutputContractError(ValueError):
    def __init__(self, message: str, *, repaired: bool = False):
        super().__init__(message)
        self.repaired = repaired


def _read_repo_file(repo_root: Path, relative: PurePosixPath, *, base_sha: str | None) -> str | None:
    if (repo_root / ".git").exists():
        for ref in ("HEAD", base_sha):
            if not ref:
                continue
            proc = subprocess.run(
                ["git", "-C", str(repo_root), "show", f"{ref}:{relative.as_posix()}"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            if proc.returncode == 0:
                return proc.stdout.decode("utf-8", errors="replace")
        return None
    path = repo_root.joinpath(*relative.parts)
    if not path.is_file() or path.is_symlink():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def _validate_repo_location(
    repo_root: Path, location: SourceLocation, *, base_sha: str | None = None
) -> None:
    relative = PurePosixPath(location.file)
    if relative.is_absolute() or ".." in relative.parts:
        raise OutputContractError(f"invalid repository-relative path: {location.file}")
    text = _read_repo_file(repo_root, relative, base_sha=base_sha)
    if text is None:
        raise OutputContractError(f"finding path does not exist in head or base snapshot: {location.file}")
    line_count = len(text.splitlines())
    if location.start_line > line_count or location.end_line > line_count:
        raise OutputContractError(
            f"line range {location.start_line}-{location.end_line} exceeds {location.file} ({line_count} lines)"
        )


def validate_agent_output(
    data: dict[str, Any], *, repo_root: str | Path | None = None, base_sha: str | None = None
) -> AgentReview:
    try:
        review = AgentReview.model_validate(data)
    except ValidationError as exc:
        raise OutputContractError(str(exc)) from exc
    if repo_root is not None:
        root = Path(repo_root).resolve()
        for finding in review.findings:
            _validate_repo_location(root, finding.location, base_sha=base_sha)
            for evidence in finding.evidence:
                _validate_repo_location(root, evidence, base_sha=base_sha)
    return review


def parse_agent_output(
    raw: str,
    *,
    repo_root: str | Path | None = None,
    allow_format_repair: bool = True,
    base_sha: str | None = None,
) -> tuple[AgentReview, bool]:
    """Parse output and perform at most one deterministic, semantics-preserving repair."""
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise OutputContractError("agent output must be a JSON object")
        return validate_agent_output(data, repo_root=repo_root, base_sha=base_sha), False
    except (json.JSONDecodeError, OutputContractError) as first_error:
        if not allow_format_repair:
            raise OutputContractError(str(first_error), repaired=False) from first_error

    repaired = repair_json_text(raw)
    if repaired is None:
        raise OutputContractError("output is invalid and deterministic format repair failed", repaired=True)
    try:
        data = json.loads(repaired)
        if not isinstance(data, dict):
            raise OutputContractError("repaired output must be a JSON object", repaired=True)
        return validate_agent_output(data, repo_root=repo_root, base_sha=base_sha), True
    except (json.JSONDecodeError, OutputContractError) as exc:
        raise OutputContractError(str(exc), repaired=True) from exc
