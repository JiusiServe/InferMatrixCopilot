"""Typed Direct-review client backed by immutable wheel resources."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import re
import threading
from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any

from ... import __version__
from .._resources import adapters_root, knowledge_root
from .models import (
    DIRECT_API_VERSION,
    KNOWLEDGE_API_VERSION,
    SDK_API_VERSION,
    STRICT_API_VERSION,
    Capabilities,
    DirectCompletionDecision,
    DirectCompletionRequest,
    DirectReviewPlan,
    DirectReviewRequest,
    DocumentNotFoundError,
    DocumentPage,
    DocumentRef,
    InvalidRequestError,
    KnowledgeRoute,
    UnsupportedRepositoryError,
)

_EXCERPT_BYTES = 64 * 1024
_DEFAULT_CONTEXT_LIMIT = 256
_FULL_SHA = re.compile(r"[0-9a-fA-F]{40}")
_CONTEXT_ID = re.compile(r"sha256:[0-9a-f]{64}")


def _distribution_version() -> str:
    try:
        installed = importlib.metadata.version("infermatrix-copilot")
    except importlib.metadata.PackageNotFoundError:
        return __version__
    # Editable environments can retain stale dist-info while importing newer
    # source.  The built-wheel smoke separately asserts metadata equality; at
    # runtime the loaded provider code must never advertise an older artifact.
    return installed if installed == __version__ else __version__


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=8)
def _resource_revision(knowledge_dir: str, adapters_dir: str) -> str:
    """Hash shipped source data, excluding interpreter-generated artifacts."""
    digest = hashlib.sha256()
    for namespace, root_value in (
        ("knowledge", knowledge_dir),
        ("adapters", adapters_dir),
    ):
        root = Path(root_value)
        digest.update(namespace.encode("utf-8"))
        digest.update(b"\0")
        paths = (
            path for path in root.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in {".pyc", ".pyo"}
        )
        for path in sorted(paths):
            digest.update(path.relative_to(root).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def get_capabilities(
    *,
    max_strict_workers: int = 1,
    supports_file_locking: bool = True,
) -> Capabilities:
    """Return the SDK/distribution/resource handshake without starting a server."""
    from .knowledge import _apply_supported

    knowledge = knowledge_root()
    adapters = adapters_root()
    repositories = tuple(sorted(
        path.name
        for path in (knowledge / "repos").iterdir()
        if path.is_dir() and (path / "_index.md").is_file()
    ))
    locking = bool(supports_file_locking)
    return Capabilities(
        distribution_version=_distribution_version(),
        sdk_api_version=SDK_API_VERSION,
        direct_api_version=DIRECT_API_VERSION,
        strict_api_version=STRICT_API_VERSION,
        knowledge_api_version=KNOWLEDGE_API_VERSION,
        resource_revision=_resource_revision(str(knowledge), str(adapters)),
        supported_repositories=repositories,
        supports_expected_head=True,
        supports_structured_result=True,
        supports_post_false=True,
        supports_file_locking=locking,
        supports_idempotent_strict_start=locking,
        supports_knowledge_curation=locking and _apply_supported(),
        max_strict_workers=int(max_strict_workers),
    )


@dataclass(frozen=True)
class _IssuedContext:
    expected_head_sha: str
    resource_revision: str


class DirectClient:
    """The supported embedded Direct-review API.

    Completion validation is intentionally bound to plans issued by this
    client instance.  The registry is bounded so a long-running review host
    cannot grow memory without limit.
    """

    def __init__(self, *, max_issued_contexts: int = _DEFAULT_CONTEXT_LIMIT) -> None:
        if max_issued_contexts < 1:
            raise InvalidRequestError("max_issued_contexts must be >= 1")
        self._knowledge = knowledge_root()
        self._adapters = adapters_root()
        self._max_issued_contexts = int(max_issued_contexts)
        self._issued_contexts: OrderedDict[str, _IssuedContext] = OrderedDict()
        self._context_lock = threading.Lock()

    @property
    def resource_revision(self) -> str:
        return _resource_revision(str(self._knowledge), str(self._adapters))

    def capabilities(self) -> Capabilities:
        return get_capabilities()

    def _document_path(self, document_id: str) -> Path:
        value = str(document_id).strip().replace("\\", "/")
        pure = PurePosixPath(value)
        if not value or pure.is_absolute() or ".." in pure.parts:
            raise DocumentNotFoundError(f"invalid document_id: {document_id!r}")
        path = (self._knowledge / pure).resolve()
        try:
            path.relative_to(self._knowledge)
        except ValueError as exc:
            raise DocumentNotFoundError(
                f"document_id escapes the knowledge bundle: {document_id!r}"
            ) from exc
        if not path.is_file():
            raise DocumentNotFoundError(f"unknown document_id: {document_id!r}")
        return path

    def _document_id(self, path_value: str | Path) -> str:
        path = Path(path_value).expanduser().resolve()
        try:
            return path.relative_to(self._knowledge).as_posix()
        except ValueError as exc:
            raise DocumentNotFoundError(
                "provider returned a document outside the packaged knowledge bundle"
            ) from exc

    def _document_ref(self, path_value: str | Path) -> DocumentRef:
        document_id = self._document_id(path_value)
        data = self._document_path(document_id).read_bytes()
        excerpt_data = data[:_EXCERPT_BYTES]
        return DocumentRef(
            document_id=document_id,
            sha256=_sha256(data),
            excerpt=excerpt_data.decode("utf-8", errors="replace"),
            truncated=len(data) > len(excerpt_data),
        )

    def read_document(
        self,
        document_id: str,
        *,
        offset: int = 0,
        max_bytes: int = _EXCERPT_BYTES,
    ) -> DocumentPage:
        if offset < 0 or max_bytes < 1 or max_bytes > _EXCERPT_BYTES:
            raise InvalidRequestError(
                "offset must be >= 0 and max_bytes must be within 1..65536"
            )
        data = self._document_path(document_id).read_bytes()
        page = data[offset:offset + max_bytes]
        next_offset = offset + len(page) if offset + len(page) < len(data) else None
        return DocumentPage(
            document_id=document_id,
            sha256=_sha256(data),
            offset=offset,
            content=page.decode("utf-8", errors="replace"),
            next_offset=next_offset,
        )

    def _request_values(self, request: DirectReviewRequest) -> tuple[str, list[str]]:
        alias = request.repository.alias.strip()
        if not request.review_id.strip():
            raise InvalidRequestError("review_id must not be empty")
        if request.pr_number < 0:
            raise InvalidRequestError("pr_number must be >= 0")
        if not alias:
            raise InvalidRequestError("repository alias must not be empty")
        if alias.replace("_", "-").casefold() not in {
            item.casefold() for item in self.capabilities().supported_repositories
        }:
            raise UnsupportedRepositoryError(f"unsupported repository: {alias!r}")
        if not _FULL_SHA.fullmatch(request.expected_head_sha.strip()):
            raise InvalidRequestError(
                "expected_head_sha must be exactly 40 hexadecimal characters"
            )

        changed_files: list[str] = []
        for item in request.changed_paths:
            value = item.path.strip().replace("\\", "/")
            path = PurePosixPath(value)
            if not value or path.is_absolute() or ".." in path.parts:
                raise InvalidRequestError(
                    f"changed path must be repository-relative: {item.path!r}"
                )
            changed_files.append(path.as_posix())
        return alias, changed_files

    def _remember_context(self, context_id: str, expected_head_sha: str) -> None:
        with self._context_lock:
            self._issued_contexts[context_id] = _IssuedContext(
                expected_head_sha=expected_head_sha,
                resource_revision=self.resource_revision,
            )
            self._issued_contexts.move_to_end(context_id)
            while len(self._issued_contexts) > self._max_issued_contexts:
                self._issued_contexts.popitem(last=False)

    def plan(self, request: DirectReviewRequest) -> DirectReviewPlan:
        # Lazy provider import is load-bearing: importing the public SDK models
        # must not import server/config modules or initialize provider runtime.
        from ...direct_routing import direct_review_plan

        alias, changed_files = self._request_values(request)
        expected_head = request.expected_head_sha.strip().casefold()
        raw = direct_review_plan(
            alias,
            title=request.title,
            body=request.body,
            changed_files=changed_files,
        )
        routes = tuple(
            KnowledgeRoute(
                owner=str(item.get("owner") or "unknown"),
                document=self._document_ref(str(item["path"])),
                reason=str(item.get("reason") or ""),
                quick_map=str(item.get("quick_map") or ""),
                quick_map_status=str(item.get("quick_map_status") or "unavailable"),
                read_required=bool(item.get("read_required")),
            )
            for item in raw.get("knowledge_routes") or []
        )
        repo_name = alias.replace("_", "-")
        map_candidates = (
            self._knowledge / "README.md",
            self._knowledge / "general" / "_index.md",
            self._knowledge / "repos" / "_index.md",
            self._knowledge / "repos" / repo_name / "_index.md",
        )
        context_payload = {
            "review_id": request.review_id,
            "repository": request.repository.to_dict(),
            "pr_number": request.pr_number,
            "expected_head_sha": expected_head,
            "title": request.title,
            "body": request.body,
            "changed_paths": [item.to_dict() for item in request.changed_paths],
            "resource_revision": self.resource_revision,
        }
        review_context_id = _sha256(json.dumps(
            context_payload, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8"))
        navigation_policy = dict(raw.get("navigation_policy") or {})
        fallback = navigation_policy.pop("fallback_entry", "")
        if fallback:
            navigation_policy["fallback_document_id"] = self._document_id(fallback)
        completion_gate = dict(raw.get("completion_gate") or {})
        completion_gate["operation"] = str(
            completion_gate.pop("tool", "") or "validate_direct_review"
        )
        plan = DirectReviewPlan(
            protocol_version=DIRECT_API_VERSION,
            review_context_id=review_context_id,
            resource_revision=self.resource_revision,
            repository=request.repository,
            expected_head_sha=expected_head,
            knowledge_entry=self._document_ref(raw["knowledge_entry"]),
            knowledge_routes=routes,
            mandatory_review_guides=tuple(
                self._document_ref(path)
                for path in raw.get("mandatory_review_guides") or []
            ),
            document_maps=tuple(
                self._document_ref(path)
                for path in map_candidates if path.is_file()
            ),
            routing=dict(raw.get("routing") or {}),
            navigation_policy=navigation_policy,
            execution_budget=dict(raw.get("execution_budget") or {}),
            first_review_checklist=tuple(raw.get("first_review_checklist") or ()),
            progress_update=dict(raw.get("progress_update") or {}),
            completion_gate=completion_gate,
            diagnostics=dict(raw.get("diagnostics") or {}),
        )
        self._remember_context(review_context_id, expected_head)
        return plan

    def validate(
        self, request: DirectCompletionRequest
    ) -> DirectCompletionDecision:
        from ...direct_routing import direct_completion_result

        missing: list[str] = []
        context_id = request.review_context_id.strip().casefold()
        expected_head = request.expected_head_sha.strip().casefold()
        evidence_head = request.evidence_head_sha.strip().casefold()
        if not _CONTEXT_ID.fullmatch(context_id):
            missing.append("review_context_id must be a provider-issued sha256 id")
        with self._context_lock:
            issued = self._issued_contexts.get(context_id)
            if issued is not None:
                self._issued_contexts.move_to_end(context_id)
        if issued is None:
            missing.append("review_context_id was not issued by this DirectClient")
        else:
            if expected_head != issued.expected_head_sha:
                missing.append(
                    "expected_head_sha does not match the issued review context"
                )
            if self.resource_revision != issued.resource_revision:
                missing.append(
                    "provider resources changed after the review context was issued"
                )
        if not _FULL_SHA.fullmatch(expected_head):
            missing.append(
                "expected_head_sha must be exactly 40 hexadecimal characters"
            )
        if expected_head != evidence_head:
            missing.append("evidence_head_sha must equal expected_head_sha")
        details: dict[str, Any] = direct_completion_result(
            subtraction_signal=request.subtraction_signal,
            subtraction=list(request.subtraction),
            minimality_proof=request.minimality_proof,
            final_comment_count=request.final_comment_count,
            evidence_head_sha=evidence_head,
            existing_feedback_status=request.existing_feedback_status,
            finding_dispositions=list(request.finding_dispositions),
        )
        missing.extend(str(item) for item in details.get("missing") or [])
        # Preserve order while avoiding duplicate explanations from overlapping
        # provider and SDK guards.
        unique_missing = tuple(dict.fromkeys(missing))
        complete = not unique_missing and bool(details.get("publish_ready"))
        return DirectCompletionDecision(
            protocol_version=DIRECT_API_VERSION,
            review_context_id=context_id,
            review_complete=complete,
            status="complete" if complete else "partial_review",
            missing=unique_missing,
            details={**details, "publish_ready": complete},
        )
