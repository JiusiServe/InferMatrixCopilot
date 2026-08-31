"""Public embedded facade for the durable Strict run lifecycle."""

from __future__ import annotations

from typing import Any, Self

from .direct import get_capabilities
from .models import (
    Capabilities,
    StrictPollResult,
    StrictReviewRequest,
    StrictRunHandle,
)


class StrictRuntime:
    """Own a durable local Strict runtime without exposing MCP internals."""

    def __init__(self, *, settings_overrides: dict[str, Any] | None = None):
        # Lazy imports keep Direct-only consumers independent of server startup
        # and make this module, not the consumer, the implementation boundary.
        from ...config import Settings
        from ...mcp_server import CopilotMCP

        self._core = CopilotMCP(Settings(**(settings_overrides or {})))

    def capabilities(self) -> Capabilities:
        raw = dict(self._core.capabilities())
        return get_capabilities(
            max_strict_workers=int(raw.get("max_strict_workers") or 1),
            supports_file_locking=bool(raw.get("supports_file_locking", True)),
        )

    def readiness(self, repo: str, repo_path: str = "") -> tuple[str, ...]:
        return tuple(self._core.strict_readiness(repo, repo_path))

    def reserve_review(self, request: StrictReviewRequest) -> StrictRunHandle:
        payload = {
            "kind": "pr_review",
            "repo": request.repository.alias,
            "pr": request.pr_number,
            "post": False,
            "params": {"review_depth": request.review_depth},
            "expected_head_sha": request.expected_head_sha,
            "repo_path": request.repo_path,
            "idempotency_key": request.idempotency_key,
        }
        run_id, created = self._core.reserve_strict_review(payload)
        return StrictRunHandle(run_id=str(run_id), created=bool(created))

    def start_review(self, request: StrictReviewRequest) -> StrictRunHandle:
        """Alias for hosts that name the reserve-and-enqueue operation start."""
        return self.reserve_review(request)

    def get_status(self, run_id: str) -> StrictPollResult:
        payload = dict(self._core.get_status(run_id))
        status = payload.get("status") or {}
        state = str(status.get("state") or payload.get("state") or "unknown")
        return StrictPollResult(run_id=run_id, state=state, payload=payload)

    def get_result(self, run_id: str, *, offset: int = 0) -> StrictPollResult:
        payload = dict(self._core.get_result(run_id, offset=offset))
        # The report content and structured result cross the SDK boundary; the
        # provider's private run-directory path does not.
        payload.pop("report_path", None)
        return StrictPollResult(
            run_id=run_id,
            state=str(payload.get("state") or "unknown"),
            payload=payload,
        )

    def close(self) -> None:
        self._core.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
