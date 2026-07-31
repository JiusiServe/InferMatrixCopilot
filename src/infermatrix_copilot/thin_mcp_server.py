"""Default MCP: Direct knowledge access plus Strict Eco-workflow compatibility."""

from __future__ import annotations

import os
import re
import signal
import sys
from pathlib import Path
from typing import Optional

from .config import Settings
from .intent import resolve_repo_alias
from .knowledge_docs import KnowledgeDocs, KnowledgeDocsError
from .mcp_policy import PolicyError
from .mcp_server import CopilotMCP

_ROOT = Path(__file__).resolve().parents[2]


def _knowledge_root() -> Path:
    override = os.environ.get("INFERMATRIX_KNOWLEDGE_DIR")
    candidates = [
        Path(override).expanduser() if override else None,
        _ROOT / "knowledge",
        Path(__file__).resolve().parent / "knowledge",
    ]
    for candidate in candidates:
        if candidate is not None and (candidate / "AGENTS.md").is_file():
            return candidate
    raise FileNotFoundError(
        "InferMatrixCopilot knowledge is missing. Reinstall the package or set "
        "INFERMATRIX_KNOWLEDGE_DIR."
    )


_KNOWLEDGE = _knowledge_root()
_PR_URL = re.compile(
    r"https?://github\.com/([\w.-]+)/([\w.-]+)/pull/(\d+)",
    re.IGNORECASE,
)
_PR_NUMBER = re.compile(r"^(?:pr\s*#?\s*)?(\d+)$", re.IGNORECASE)
_REPO_ALIASES = {
    "vllm-project/vllm-omni": "vllm-omni",
}
_DIRECT_REVIEW_CHECKLIST = [
    "Freeze one base/head snapshot and collect PR intent, diff, mergeability, and CI once.",
    "Route PR title/body to exact owner/model rules; use changed files only to validate scope.",
    "Reuse one evidence packet for callers, tests, correctness findings, and design/subtraction.",
    "Complete a bounded subtraction pass before finalizing, even when correctness bugs were found.",
    "Plan exactly one consolidated final review comment.",
]
_SUBTRACTION_ACTIONS = {"DELETE", "DEFER", "INLINE", "MERGE", "MOVE"}


def _normalize_repo(repo: str) -> str:
    selected = str(repo or "vllm-omni").strip()
    return _REPO_ALIASES.get(selected.casefold(), selected)


def _supported_repos() -> list[str]:
    if not (_KNOWLEDGE / "repos").is_dir():
        return []
    return sorted(
        path.name for path in (_KNOWLEDGE / "repos").iterdir()
        if path.is_dir() and (path / "_index.md").is_file()
    )


def _docs(repo: str) -> KnowledgeDocs:
    repo = _normalize_repo(repo)
    repo_dir = _KNOWLEDGE / "repos" / repo
    if not repo_dir.is_dir():
        raise KnowledgeDocsError(f"unsupported knowledge repo: {repo}")
    return KnowledgeDocs(_KNOWLEDGE, f"repos/{repo}")


def _guard(fn):
    try:
        return fn()
    except (KnowledgeDocsError, FileNotFoundError, PolicyError, ValueError) as exc:
        return {"error": str(exc)}


def _knowledge_entry(name: str) -> str:
    path = (_KNOWLEDGE / name).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"knowledge entry is missing: {path}")
    return str(path)


def _direct_completion_result(
    subtraction: Optional[list[dict[str, str]]] = None,
    minimality_proof: Optional[dict[str, str]] = None,
    final_comment_count: int = 1,
) -> dict:
    """Mechanically gate Direct completion on subtraction evidence.

    This deliberately checks structure, not whether the review evidence is
    true. The host still owns the code review, but cannot call a bug-only
    result complete without either actionable subtraction or a concrete
    explanation of why the inspected scope is already minimal.
    """
    subtraction = subtraction or []
    minimality_proof = minimality_proof or {}
    missing: list[str] = []

    if final_comment_count != 1:
        missing.append("final_comment_count must be exactly 1")

    malformed_subtractions: list[int] = []
    for index, item in enumerate(subtraction):
        if not isinstance(item, dict):
            malformed_subtractions.append(index)
            continue
        anchor = str(item.get("anchor", "")).strip()
        action = str(item.get("action", "")).strip()
        risk = str(item.get("risk", "")).strip()
        action_kind = action.split(maxsplit=1)[0].upper() if action else ""
        if (
            ":" not in anchor
            or action_kind not in _SUBTRACTION_ACTIONS
            or not risk
        ):
            malformed_subtractions.append(index)
    if malformed_subtractions:
        missing.append(
            "each subtraction item needs a path:line anchor, a "
            "DELETE/DEFER/INLINE/MERGE/MOVE action, and a non-empty risk "
            f"(invalid indexes: {malformed_subtractions})"
        )

    has_subtraction = bool(subtraction) and not malformed_subtractions
    proof_fields = (
        "scope_ledger",
        "abstraction_census",
        "why_no_safe_deletion",
    )
    has_minimality_proof = all(
        len(str(minimality_proof.get(field, "")).strip()) >= 12
        for field in proof_fields
    )
    if not has_subtraction and not has_minimality_proof:
        missing.append(
            "provide subtraction items or a concrete minimality_proof with "
            "scope_ledger, abstraction_census, and why_no_safe_deletion"
        )

    complete = not missing
    return {
        "status": "complete" if complete else "partial_review",
        "publish_ready": complete,
        "final_comment_count": final_comment_count,
        "subtraction_items": len(subtraction),
        "minimality_proof": has_minimality_proof,
        "missing": missing,
        "next_action": (
            "Return the single consolidated review comment."
            if complete
            else "Run one bounded subtraction pass using the existing evidence packet, then validate again."
        ),
    }


def _strict_review_request(
    target: str,
    repo: str,
    *,
    post: bool,
    review_depth: str,
    settings: Settings,
) -> dict:
    """Translate the Strict public surface to the previous Eco TaskSpec shape."""
    target = str(target).strip()
    if not target:
        raise ValueError("target must not be empty")
    if not isinstance(post, bool):
        raise ValueError("post must be a boolean")

    match = _PR_URL.search(target)
    if match:
        owner, name, number = match.groups()
        selected_repo = resolve_repo_alias(owner, name, settings)
        selected_repo = selected_repo or _REPO_ALIASES.get(
            f"{owner}/{name}".casefold())
        if selected_repo is None:
            raise ValueError(
                f"repository {owner}/{name} is not configured for Strict mode")
        pr = int(number)
    else:
        match = _PR_NUMBER.fullmatch(target)
        if not match:
            raise ValueError("Strict mode requires a PR URL or number")
        selected_repo = _normalize_repo(repo or settings.default_repo)
        pr = int(match.group(1))

    request = {
        "kind": "pr_review",
        "repo": selected_repo,
        "pr": pr,
        "mode": "eco",
        "post": post,
    }
    if review_depth:
        request["params"] = {"review_depth": review_depth}
    return request


def build_mcp(
    settings: Optional[Settings] = None,
    core: Optional[CopilotMCP] = None,
):
    from mcp.server.fastmcp import FastMCP

    core = core or CopilotMCP(settings)
    mcp = FastMCP(
        "infermatrix-copilot",
        instructions=(
            "Use review in direct mode unless the user explicitly requests "
            "Strict. Direct returns a knowledge entry and compact first-review "
            "checklist for the host model. Before treating a Direct review as "
            "complete or posting its only final comment, call "
            "validate_direct_review. A partial_review result requires one "
            "bounded subtraction pass using the existing evidence packet. "
            "Strict is the previous Eco workflow under a new public name: it "
            "runs the configured workflow model, returns a run_id, and must be "
            "polled with get_review_result until terminal. Posting is never "
            "implicit; pass post=true only when the user explicitly asks."
        ),
    )

    @mcp.tool()
    def review(
        target: str,
        repo: str = "vllm-omni",
        mode: str = "direct",
        post: bool = False,
        review_depth: str = "",
    ) -> dict:
        """Begin a Direct or Strict review.

        Direct returns the knowledge entrypoint for the host model. Strict
        runs the previous Eco PR-review workflow. ``post`` still requires both
        explicit user intent and server-side ``ALLOW_POST=1``.
        """
        def run() -> dict:
            if not str(target).strip():
                raise ValueError("target must not be empty")
            selected_mode = str(mode).strip().casefold() or "direct"
            if selected_mode not in {"direct", "strict"}:
                raise ValueError("mode must be 'direct' or 'strict'")
            if selected_mode == "direct":
                return {
                    "mode": "direct",
                    "knowledge_entry": _knowledge_entry("AGENTS.md"),
                    "first_review_checklist": list(_DIRECT_REVIEW_CHECKLIST),
                    "completion_gate": {
                        "tool": "validate_direct_review",
                        "require_one_of": [
                            "subtraction[{anchor, action, risk}]",
                            "minimality_proof{scope_ledger, abstraction_census, why_no_safe_deletion}",
                        ],
                        "final_comment_count": 1,
                        "if_missing": "partial_review",
                    },
                }

            request = _strict_review_request(
                target, repo, post=post, review_depth=review_depth,
                settings=core.settings)
            return {
                "run_id": core.start_strict_review(request),
                "mode": "strict",
                "execution_mode": "eco",
                "post": request["post"],
            }

        return _guard(run)

    @mcp.tool()
    def validate_direct_review(
        subtraction: Optional[list[dict[str, str]]] = None,
        minimality_proof: Optional[dict[str, str]] = None,
        final_comment_count: int = 1,
    ) -> dict:
        """Validate the Direct completion gate before the only final comment.

        Supply actionable subtraction items when safe deletion, merge, inline,
        or scope deferral exists. Otherwise supply concrete scope-ledger and
        abstraction-census evidence explaining why no safe deletion remains.
        A ``partial_review`` result is not a completed Direct review.
        """
        return _direct_completion_result(
            subtraction=subtraction,
            minimality_proof=minimality_proof,
            final_comment_count=final_comment_count,
        )

    @mcp.tool()
    def get_review_result(run_id: str, offset: int = 0) -> dict:
        """Poll a Strict run and page its final report with ``next_offset``."""
        return _guard(lambda: {
            "mode": "strict",
            **core.get_result(run_id, offset),
        })

    @mcp.tool()
    def get_review_status(run_id: str) -> dict:
        """Return the old workflow's durable status and step progress."""
        return _guard(lambda: {
            "mode": "strict",
            **core.get_status(run_id),
        })

    @mcp.tool()
    def update_knowledge(repo: str = "vllm-omni") -> dict:
        """Return the knowledge contribution entrypoint for the host to follow."""
        return _guard(lambda: {
            "knowledge_entry": _knowledge_entry("CONTRIBUTING.md")
        })

    @mcp.tool()
    def doc_search(
        query: str,
        repo: str = "vllm-omni",
        limit: int = 20,
    ) -> dict:
        """Search knowledge; repo accepts a short name or canonical owner/name."""
        def run() -> dict:
            selected_repo = _normalize_repo(repo)
            if selected_repo not in _supported_repos():
                supported = ", ".join(_supported_repos()) or "(none)"
                return {
                    "error": (
                        f"unsupported knowledge repo: {repo}. "
                        f"Supported: {supported}."
                    )
                }
            matches = _docs(selected_repo).search(query, limit=limit)
            return {
                "query": query,
                "repo": selected_repo,
                "matches": matches,
            }

        return _guard(run)

    @mcp.tool()
    def doc_read(
        path: str,
        repo: str = "vllm-omni",
        offset: int = 0,
    ) -> dict:
        """Read a doc_search page; repo accepts a short or canonical owner/name."""
        def run() -> dict:
            selected_repo = _normalize_repo(repo)
            return {
                "repo": selected_repo,
                **_docs(selected_repo).read(path, offset=offset),
            }

        return _guard(run)

    return mcp


def main() -> int:
    if sys.platform == "win32":
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        mcp = build_mcp()
    except ImportError:
        sys.stderr.write(
            "infermatrix-copilot-mcp needs the MCP SDK. Install with "
            "pip install -e '.[mcp]'\n"
        )
        return 1
    mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
