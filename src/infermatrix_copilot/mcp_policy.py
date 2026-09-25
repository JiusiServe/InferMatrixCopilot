"""Compatibility imports for the original MCP policy module.

Request validation is owned by the headless application because the SDK and
reserved-run worker apply the same gates as the MCP transport.
"""

from .app.request_policy import (
    PolicyError,
    authorize_repo_path,
    enforce_mcp_policy,
    enforce_quality_review_policy,
    enforce_strict_review_policy,
)

__all__ = [
    "PolicyError",
    "authorize_repo_path",
    "enforce_mcp_policy",
    "enforce_quality_review_policy",
    "enforce_strict_review_policy",
]
