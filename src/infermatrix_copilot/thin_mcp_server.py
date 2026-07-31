"""Default MCP: Direct knowledge access plus the Strict review workflow."""

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
_DIRECT_OWNER_ROUTES = (
    {
        "owner": "configuration",
        "path": "repos/vllm-omni/components/configuration/rules.md",
        "signals": (
            "config",
            "configuration",
            "yaml",
            "registry",
            "deploy",
            "pipeline",
            "override",
            "default",
            "cli flag",
            "topology",
        ),
        "scope_prefixes": (
            "vllm_omni/config/",
            "vllm_omni/deploy/",
        ),
    },
    {
        "owner": "serving",
        "path": "repos/vllm-omni/components/serving/rules.md",
        "signals": (
            "serving",
            "server",
            "endpoint",
            "openai",
            "request",
            "response",
            "http",
            "chat completion",
            "completion endpoint",
            "speech api",
            "sse",
            "websocket",
            "sleep",
            "wake",
            "partial wake",
            "engine lifecycle",
            "idempotency",
            "ack",
        ),
        "scope_prefixes": (
            "vllm_omni/entrypoints/openai/",
            "vllm_omni/entrypoints/api_server.py",
            "vllm_omni/entrypoints/async_omni.py",
        ),
    },
    {
        "owner": "model-executor",
        "path": "repos/vllm-omni/components/model-executor/rules.md",
        "signals": (
            "model executor",
            "loader",
            "checkpoint",
            "tokenizer",
            "processor",
            "stage input",
            "stage handoff",
            "runtime info",
            "runtime_info",
            "batch",
            "sampling",
        ),
        "scope_prefixes": (
            "vllm_omni/model_executor/",
            "vllm_omni/inputs/",
        ),
    },
    {
        "owner": "diffusion",
        "path": "repos/vllm-omni/components/diffusion/rules.md",
        "signals": (
            "diffusion",
            "image generation",
            "text to image",
            "image to image",
            "lora",
            "vae",
            "dit",
            "ulysses",
            "cache dit",
        ),
        "scope_prefixes": (
            "vllm_omni/diffusion/",
            "vllm_omni/model_executor/models/diffusers/",
        ),
    },
    {
        "owner": "distributed",
        "path": "repos/vllm-omni/components/distributed/_index.md",
        "signals": (
            "distributed",
            "tensor parallel",
            "data parallel",
            "replica",
            "collective",
            "rpc",
        ),
        "scope_prefixes": (
            "vllm_omni/distributed/",
            "vllm_omni/worker/",
            "vllm_omni/entrypoints/async_omni.py",
        ),
    },
    {
        "owner": "scheduler",
        "path": "repos/vllm-omni/components/scheduler/rules.md",
        "signals": (
            "scheduler",
            "scheduling",
            "prefix cache",
            "token budget",
            "queue",
            "side stream",
        ),
        "scope_prefixes": (
            "vllm_omni/core/sched/",
            "vllm_omni/diffusion/sched/",
        ),
    },
)
_DIRECT_REVIEW_CHECKLIST = [
    "Freeze one base/head snapshot and collect PR intent, diff, mergeability, and CI once.",
    "Immediately after snapshot metadata returns, report head SHA, CI, mergeability, and preliminary findings in the host conversation; do this before reading knowledge, searching source, or running tests.",
    "Call Direct once with the collected title, body, and changed_files; read only the returned knowledge_routes and stop knowledge navigation.",
    "After the progress update, run independent knowledge/source and validation tracks concurrently.",
    "Reuse one in-review evidence packet for files, bounded rg searches, callers, tests, repo-map, routing, and findings.",
    "Treat CI as status only; open logs only when the first failure overlaps the frozen diff or blocks the verdict.",
    "For docs-only changes, skip dependency preflight and pytest; use diff hygiene plus bounded checks of the referenced live contract.",
    "Before pytest, run a short import/version compatibility preflight; bind commands and results to head SHA and an environment fingerprint.",
    "After preflight passes, run targeted tests and low-cost static checks alongside source review.",
    "Stop investigating when every changed semantic path has a supported finding or explicit no-issue conclusion; do not add searches only for confidence.",
    "Run subtraction only when the diff adds or expands a helper, class, fallback, compatibility branch, or public behavior; otherwise mark no subtraction signal.",
    "Plan exactly one consolidated final review comment.",
]
_DIRECT_PROGRESS_UPDATE = {
    "deadline_seconds": 60,
    "channel": "host_conversation",
    "required_fields": [
        "head_sha",
        "ci_status",
        "mergeability",
        "early_findings",
    ],
    "early_findings_status": "preliminary",
    "continue_review": True,
    "github_comment": False,
    "emit_before": [
        "knowledge_read",
        "source_search",
        "tests",
    ],
    "do_not_wait_for": [
        "ci_completion",
        "mergeability_resolution",
    ],
}
_SUBTRACTION_ACTIONS = {"DELETE", "DEFER", "INLINE", "MERGE", "MOVE"}
_SUBTRACTION_SIGNALS = {"none", "triggered"}


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


def _knowledge_path(relative_path: str) -> str:
    path = (_KNOWLEDGE / relative_path).resolve()
    try:
        path.relative_to(_KNOWLEDGE.resolve())
    except ValueError as exc:
        raise ValueError(
            f"knowledge route escapes the knowledge root: {relative_path}"
        ) from exc
    if not path.is_file():
        raise FileNotFoundError(f"knowledge route is missing: {path}")
    return str(path)


def _route_text(value: str) -> str:
    normalized = re.sub(r"[_./-]+", " ", str(value).casefold())
    return re.sub(r"\s+", " ", normalized).strip()


def _signal_matches(text: str, signal: str) -> bool:
    normalized = _route_text(signal)
    return bool(
        re.search(
            rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])",
            text,
        )
    )


def _direct_quick_map(path: str, max_chars: int = 3500) -> str:
    """Return only the embedded Direct code map, never the whole rule page."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    start = next(
        (
            index for index, line in enumerate(lines)
            if re.match(r"^##\s+.*Direct", line, re.IGNORECASE)
        ),
        None,
    )
    if start is None:
        return ""
    end = next(
        (
            index for index in range(start + 1, len(lines))
            if lines[index].startswith("## ")
        ),
        len(lines),
    )
    excerpt = "\n".join(lines[start:end]).strip()
    if len(excerpt) <= max_chars:
        return excerpt
    return excerpt[:max_chars].rsplit("\n", 1)[0].rstrip()


def _direct_execution_budget(changed_files: list[str]) -> dict:
    normalized = [path.replace("\\", "/").casefold() for path in changed_files]
    docs_only = bool(normalized) and all(
        path.startswith(("docs/", "doc/", "recipes/"))
        or path.endswith((".md", ".mdx", ".rst", ".txt"))
        for path in normalized
    )
    return {
        "profile": "docs_only" if docs_only else "code",
        "knowledge_file_reads": 0,
        "initial_source_files": 6,
        "search_matches_per_query": 40,
        "command_output_chars": 12000,
        "validation_commands": 2 if docs_only else 4,
        "total_command_calls": 12 if docs_only else 20,
        "hard_ceiling": True,
        "extension_command_calls": 4,
        "on_limit": (
            "Stop and return the supported verdict plus remaining validation "
            "gap unless the bounded extension condition is met."
        ),
        "extension": (
            "One bounded extension is allowed only for a concrete unresolved "
            "P1/high-risk contract; state the question before extending."
        ),
    }


def _direct_knowledge_routes(
    repo: str,
    *,
    title: str = "",
    body: str = "",
    changed_files: Optional[list[str]] = None,
) -> dict:
    """Select bounded Direct knowledge routes from PR intent.

    Title/body select owners. Changed files only report whether the frozen diff
    supports or contradicts that selection; they never silently replace it.
    """
    selected_repo = _normalize_repo(repo)
    changed_files = changed_files or []
    if not isinstance(changed_files, list) or any(
        not isinstance(path, str) for path in changed_files
    ):
        raise ValueError("changed_files must be a list of paths")

    intent = _route_text(f"{title}\n{body}")
    if not intent:
        return {
            "status": "needs_pr_context",
            "selected_by": "title_body",
            "required": ["title", "body", "changed_files"],
            "changed_files_role": "scope_validation_only",
            "routes": [],
            "scope_validation": [],
        }
    if selected_repo != "vllm-omni":
        return {
            "status": "unsupported_exact_router",
            "selected_by": "title_body",
            "changed_files_role": "scope_validation_only",
            "routes": [],
            "scope_validation": [],
        }

    owner_routes: list[dict[str, object]] = []
    for route in _DIRECT_OWNER_ROUTES:
        matched = [
            signal for signal in route["signals"]
            if _signal_matches(intent, signal)
        ]
        if matched:
            path = _knowledge_path(str(route["path"]))
            owner_routes.append({
                "owner": str(route["owner"]),
                "path": path,
                "reason": f"title/body: {', '.join(matched[:3])}",
                "quick_map": _direct_quick_map(path),
                "read_required": False,
            })

    model_routes: list[dict[str, object]] = []
    model_root = _KNOWLEDGE / "repos" / "vllm-omni" / "models"
    for model_dir in sorted(model_root.iterdir(), key=lambda path: -len(path.name)):
        rules = model_dir / "rules.md"
        if not rules.is_file():
            continue
        model_name = _route_text(model_dir.name)
        compact_name = re.sub(r"[^a-z0-9]", "", model_name)
        compact_intent = re.sub(r"[^a-z0-9]", "", intent)
        exact_match = _signal_matches(intent, model_name)
        compact_match = len(compact_name) >= 8 and compact_name in compact_intent
        if exact_match or compact_match:
            path = str(rules.resolve())
            model_routes.append({
                "owner": f"model:{model_dir.name}",
                "path": path,
                "reason": f"title/body model: {model_dir.name}",
                "quick_map": _direct_quick_map(path),
                "read_required": False,
            })

    routes = (model_routes + owner_routes)[:3]
    scope_validation = []
    for route in _DIRECT_OWNER_ROUTES:
        hits = sorted({
            path for path in changed_files
            if any(
                path.replace("\\", "/").startswith(prefix)
                for prefix in route["scope_prefixes"]
            )
        })
        if hits:
            scope_validation.append({
                "owner": route["owner"],
                "changed_files": hits,
                "selected_from_description": any(
                    item["owner"] == route["owner"] for item in owner_routes
                ),
            })

    return {
        "status": "ready" if routes else "description_unrouted",
        "selected_by": "title_body",
        "changed_files_role": "scope_validation_only",
        "routes": routes,
        "scope_validation": scope_validation,
    }


def _direct_completion_result(
    subtraction_signal: str = "",
    subtraction: Optional[list[dict[str, str]]] = None,
    minimality_proof: Optional[dict[str, str]] = None,
    final_comment_count: int = 1,
) -> dict:
    """Mechanically gate Direct completion on subtraction classification.

    This deliberately checks structure, not whether the review evidence is
    true. A diff without a subtraction trigger can finish after explicitly
    declaring ``none``. Triggered diffs still need actionable subtraction or
    concrete evidence that the inspected scope is already minimal.
    """
    subtraction_signal = str(subtraction_signal).strip().casefold()
    subtraction = subtraction or []
    minimality_proof = minimality_proof or {}
    missing: list[str] = []

    if final_comment_count != 1:
        missing.append("final_comment_count must be exactly 1")

    if subtraction_signal not in _SUBTRACTION_SIGNALS:
        missing.append("subtraction_signal must be 'none' or 'triggered'")

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
    if (
        subtraction_signal == "none"
        and (subtraction or minimality_proof)
    ):
        missing.append(
            "subtraction_signal 'none' cannot include subtraction evidence"
        )
    elif (
        subtraction_signal == "triggered"
        and not has_subtraction
        and not has_minimality_proof
    ):
        missing.append(
            "triggered subtraction requires subtraction items or a concrete "
            "minimality_proof with "
            "scope_ledger, abstraction_census, and why_no_safe_deletion"
        )

    complete = not missing
    return {
        "status": "complete" if complete else "partial_review",
        "publish_ready": complete,
        "final_comment_count": final_comment_count,
        "subtraction_signal": subtraction_signal,
        "subtraction_required": subtraction_signal == "triggered",
        "subtraction_items": len(subtraction),
        "minimality_proof": has_minimality_proof,
        "missing": missing,
        "next_action": (
            "Return the single consolidated review comment."
            if complete
            else "Classify the subtraction signal; only a triggered diff needs one bounded subtraction pass using the existing evidence packet."
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
    """Translate the Strict public surface to the internal review TaskSpec."""
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
            "Strict. For Direct, first freeze the PR snapshot and report head "
            "SHA, CI, mergeability, and preliminary findings in the host "
            "conversation. Do not read knowledge or source before that update. "
            "Then call review once with title, body, and changed_files. Direct "
            "returns at most three exact knowledge routes with embedded quick "
            "maps; use those excerpts and do not open full rule pages unless a "
            "concrete ambiguity blocks source review. Follow the returned "
            "execution_budget as a hard ceiling; stop with the supported "
            "verdict at the limit. Extend it once by the returned allowance "
            "only for a stated unresolved P1/high-risk contract. Continue "
            "reviewing without "
            "posting an early GitHub comment. Before treating a Direct review as "
            "complete or posting its only final comment, call "
            "validate_direct_review. Mark subtraction_signal=none when the diff "
            "does not add or expand a helper, class, fallback, compatibility "
            "branch, or public behavior. Only subtraction_signal=triggered "
            "requires subtraction evidence. "
            "Strict runs the packaged background review workflow with the "
            "configured model, returns a run_id, and must be "
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
        title: str = "",
        body: str = "",
        changed_files: Optional[list[str]] = None,
        repo_path: str = "",
    ) -> dict:
        """Begin a Direct or Strict review.

        For Direct, first collect the frozen PR title, body, and changed files,
        publish the host progress update, then pass that context here. Direct
        returns at most three exact owner/model routes; changed files only
        validate scope. Strict runs the packaged PR-review workflow and accepts
        an optional local checkout through ``repo_path``. ``post`` still
        requires explicit intent and server-side ``ALLOW_POST=1``.
        """
        def run() -> dict:
            if not str(target).strip():
                raise ValueError("target must not be empty")
            selected_mode = str(mode).strip().casefold() or "direct"
            if selected_mode not in {"direct", "strict"}:
                raise ValueError("mode must be 'direct' or 'strict'")
            if selected_mode == "direct":
                routing = _direct_knowledge_routes(
                    repo,
                    title=title,
                    body=body,
                    changed_files=changed_files,
                )
                knowledge_routes = routing["routes"]
                knowledge_entry = (
                    knowledge_routes[0]["path"]
                    if knowledge_routes
                    else _knowledge_entry("AGENTS.md")
                )
                return {
                    "mode": "direct",
                    "knowledge_entry": knowledge_entry,
                    "knowledge_routes": knowledge_routes,
                    "routing": {
                        key: value for key, value in routing.items()
                        if key != "routes"
                    },
                    "navigation_policy": {
                        "progress_before_knowledge": True,
                        "use_embedded_quick_maps": True,
                        "open_route_file_only_for_concrete_ambiguity": True,
                        "max_routes": 3,
                        "stop_after_routes": True,
                        "fallback_entry": _knowledge_entry("AGENTS.md"),
                    },
                    "execution_budget": _direct_execution_budget(
                        changed_files or []
                    ),
                    "first_review_checklist": list(_DIRECT_REVIEW_CHECKLIST),
                    "progress_update": {
                        **_DIRECT_PROGRESS_UPDATE,
                        "required_fields": list(
                            _DIRECT_PROGRESS_UPDATE["required_fields"]
                        ),
                    },
                    "completion_gate": {
                        "tool": "validate_direct_review",
                        "subtraction_signal": {
                            "none": "No helper/class/fallback/compatibility/public-behavior expansion; no subtraction evidence required.",
                            "triggered": "Require subtraction items or minimality_proof.",
                        },
                        "triggered_require_one_of": [
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
            core.configure_strict_repo(request["repo"], repo_path)
            missing = core.strict_readiness(request["repo"])
            if missing:
                raise ValueError(
                    "Strict mode is not ready: " + "; ".join(missing)
                )
            return {
                "run_id": core.start_strict_review(request),
                "mode": "strict",
                "execution_mode": "eco",
                "post": request["post"],
            }

        return _guard(run)

    @mcp.tool()
    def validate_direct_review(
        subtraction_signal: str = "",
        subtraction: Optional[list[dict[str, str]]] = None,
        minimality_proof: Optional[dict[str, str]] = None,
        final_comment_count: int = 1,
    ) -> dict:
        """Validate the Direct completion gate before the only final comment.

        Use ``subtraction_signal='none'`` when the diff does not add or expand a
        helper, class, fallback, compatibility branch, or public behavior. Use
        ``'triggered'`` for those diffs, then supply actionable subtraction
        items or concrete minimality evidence. A ``partial_review`` result is
        not a completed Direct review.
        """
        return _direct_completion_result(
            subtraction_signal=subtraction_signal,
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
        """Return a Strict run's durable status and step progress."""
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
