"""Immutable, serializable SDK v1 contract models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SDK_API_VERSION = "1.0.0"
DIRECT_API_VERSION = "1.0.0"
STRICT_API_VERSION = "1.0.0"
QUALITY_API_VERSION = "1.0.0"
KNOWLEDGE_API_VERSION = "1.0.0"


class _Serializable:
    """Lossless Python-wire projection shared by all public data models."""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)  # type: ignore[arg-type]


class SDKError(RuntimeError):
    """Base error whose code is stable across implementation releases."""

    code = "sdk_error"


class InvalidRequestError(SDKError):
    code = "invalid_request"


class IncompatibleVersionError(SDKError):
    code = "incompatible_version"


class UnsupportedRepositoryError(SDKError):
    code = "unsupported_repository"


class DocumentNotFoundError(SDKError):
    code = "document_not_found"


class KnowledgeCurationError(SDKError):
    code = "knowledge_curation_error"


@dataclass(frozen=True)
class RepositoryRef(_Serializable):
    alias: str
    full_name: str = ""


@dataclass(frozen=True)
class ChangedPath(_Serializable):
    path: str
    status: str = ""


@dataclass(frozen=True)
class DocumentRef(_Serializable):
    document_id: str
    sha256: str
    excerpt: str
    truncated: bool


@dataclass(frozen=True)
class DocumentPage(_Serializable):
    document_id: str
    sha256: str
    offset: int
    content: str
    next_offset: int | None


@dataclass(frozen=True)
class KnowledgeRoute(_Serializable):
    owner: str
    document: DocumentRef
    reason: str
    quick_map: str
    quick_map_status: str
    read_required: bool


@dataclass(frozen=True)
class KnowledgeEvidenceEvent(_Serializable):
    """One host-collected, untrusted fact bundle offered for distillation."""

    event_id: str
    source_kind: str
    source_reference: str
    title: str
    summary: str = ""
    changed_paths: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeEvidenceBatch(_Serializable):
    """One bounded curation request; orchestration remains host-owned."""

    batch_id: str
    repository: RepositoryRef
    events: tuple[KnowledgeEvidenceEvent, ...]
    max_rules: int = 8


@dataclass(frozen=True)
class KnowledgeRuleProposal(_Serializable):
    """A mechanically validated append-only rule proposal."""

    proposal_id: str
    input_index: int
    page_document_id: str
    rule_id: str
    section_markdown: str
    sources: tuple[str, ...]
    page_sha256: str


@dataclass(frozen=True)
class KnowledgeProposalRejection(_Serializable):
    index: int
    reason: str


@dataclass(frozen=True)
class KnowledgeProposalValidation(_Serializable):
    batch_id: str
    repository: RepositoryRef
    accepted: tuple[KnowledgeRuleProposal, ...]
    rejected: tuple[KnowledgeProposalRejection, ...]


@dataclass(frozen=True)
class KnowledgeValidatorResult(_Serializable):
    validator_id: str
    passed: bool
    status: str
    returncode: int | None
    output: str


@dataclass(frozen=True)
class KnowledgeApplyResult(_Serializable):
    batch_id: str
    success: bool
    attempted: int
    applied: int
    accepted_indexes: tuple[int, ...]
    rejected_indexes: tuple[int, ...]
    updated_document_ids: tuple[str, ...]
    updated_on: str
    validators: tuple[KnowledgeValidatorResult, ...]
    rolled_back: bool


@dataclass(frozen=True)
class Capabilities(_Serializable):
    distribution_version: str
    sdk_api_version: str
    direct_api_version: str
    strict_api_version: str
    quality_api_version: str
    knowledge_api_version: str
    resource_revision: str
    supported_repositories: tuple[str, ...]
    supports_expected_head: bool
    supports_structured_result: bool
    supports_post_false: bool
    supports_file_locking: bool
    supports_idempotent_strict_start: bool
    supports_quality_review: bool
    supports_knowledge_curation: bool
    max_strict_workers: int


@dataclass(frozen=True)
class DirectReviewRequest(_Serializable):
    review_id: str
    repository: RepositoryRef
    pr_number: int
    expected_head_sha: str
    title: str
    body: str
    changed_paths: tuple[ChangedPath, ...]


@dataclass(frozen=True)
class DirectReviewPlan(_Serializable):
    protocol_version: str
    review_context_id: str
    resource_revision: str
    repository: RepositoryRef
    expected_head_sha: str
    knowledge_entry: DocumentRef
    knowledge_routes: tuple[KnowledgeRoute, ...]
    mandatory_review_guides: tuple[DocumentRef, ...]
    document_maps: tuple[DocumentRef, ...]
    routing: dict[str, Any]
    navigation_policy: dict[str, Any]
    execution_budget: dict[str, Any]
    first_review_checklist: tuple[str, ...]
    progress_update: dict[str, Any]
    completion_gate: dict[str, Any]
    diagnostics: dict[str, Any] = field(default_factory=dict)

FeedbackStatus = Literal[
    "checked", "disabled", "unavailable", "not_applicable"
]


@dataclass(frozen=True)
class DirectCompletionRequest(_Serializable):
    review_context_id: str
    expected_head_sha: str
    evidence_head_sha: str
    subtraction_signal: str
    subtraction: tuple[dict[str, str], ...] = ()
    minimality_proof: dict[str, str] | None = None
    final_comment_count: int = 1
    existing_feedback_status: FeedbackStatus = "not_applicable"
    finding_dispositions: tuple[dict[str, str], ...] = ()


@dataclass(frozen=True)
class DirectCompletionDecision(_Serializable):
    protocol_version: str
    review_context_id: str
    review_complete: bool
    status: str
    missing: tuple[str, ...]
    details: dict[str, Any]

@dataclass(frozen=True)
class StrictReviewRequest(_Serializable):
    repository: RepositoryRef
    pr_number: int
    expected_head_sha: str
    repo_path: str
    idempotency_key: str
    review_depth: str = "standard"


@dataclass(frozen=True)
class StrictRunHandle(_Serializable):
    run_id: str
    created: bool


@dataclass(frozen=True)
class StrictPollResult(_Serializable):
    run_id: str
    state: str
    payload: dict[str, Any]

    @property
    def terminal(self) -> bool:
        return self.state not in {"queued", "planning", "running"}


@dataclass(frozen=True)
class QualityReviewRequest(_Serializable):
    repository: RepositoryRef
    pr_number: int
    expected_head_sha: str
    repo_path: str
    idempotency_key: str
    deterministic_signals: tuple[str, ...] = ()


@dataclass(frozen=True)
class QualityRunHandle(_Serializable):
    run_id: str
    created: bool


@dataclass(frozen=True)
class QualityPollResult(_Serializable):
    run_id: str
    state: str
    payload: dict[str, Any]

    @property
    def terminal(self) -> bool:
        return self.state not in {"queued", "planning", "running"}
