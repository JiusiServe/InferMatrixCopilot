"""Direct-mode knowledge routing: the tables and the routing mechanism.

Its four entry points — `direct_knowledge_routes`, `direct_execution_budget`,
`direct_completion_result`, `direct_mandatory_review_guides` — are re-exported by
`contract.py`, which is the surface consumers import. They live here rather than
there because the routing tables below are repo-specific knowledge, and the
public contract module must stay repo-neutral (invariant 6). This module carries
that debt, inherited verbatim from `thin_mcp_server.py` where it used to sit;
extracting the tables into `adapters/<repo>/` is the pending cleanup, unchanged
by this move.

They were moved out of `thin_mcp_server.py` because a downstream consumer
imported the four `_direct_*` privates from it through `importlib` — a coupling
that broke another repository at runtime whenever a server-module symbol was
renamed, with no build-time signal.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from .adapters import AdapterError, AdapterRegistry, RepoAdapter


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


_ADAPTERS = _ROOT / "adapters"
_REPO_ALIASES = {
    "vllm-project/vllm-omni": "vllm-omni",
    "vllm-project/afd-plugin": "afd-plugin",
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
        ),
    },
)


_DIRECT_MANDATORY_REVIEW_GUIDES = (
    "general/review/guides/simplification-audit.md",
)


_SUBTRACTION_ACTIONS = {"DELETE", "DEFER", "INLINE", "MERGE", "MOVE"}
_SUBTRACTION_SIGNALS = {"none", "triggered"}
_FEEDBACK_STATUSES = {"checked", "disabled", "unavailable", "not_applicable"}
_RESOLVED_HEAD_RECHECKS = {"fixed", "still_affected"}
_FINDING_DISPOSITIONS = {
    "new",
    "duplicate",
    "extends_existing",
    "resolved_or_outdated",
}
_EVIDENCE_HEAD_SHA = re.compile(r"[0-9a-f]{7,40}")


def _normalize_repo(repo: str) -> str:
    selected = str(repo or "vllm-omni").strip()
    alias = _REPO_ALIASES.get(selected.casefold())
    if alias:
        return alias
    adapter = _adapter_for_repo(selected)
    if adapter is not None:
        repo_subdir = str(
            (adapter.manifest.get("knowledge") or {}).get("repo_subdir") or "")
        if repo_subdir.startswith("repos/"):
            return repo_subdir.removeprefix("repos/").strip("/")
        return adapter.name.replace("_", "-")
    return selected.replace("_", "-")


def _adapter_for_repo(repo: str) -> RepoAdapter | None:
    try:
        return AdapterRegistry(_ADAPTERS).resolve(name=repo)
    except AdapterError:
        return None


def _adapter_changed_file_routes(
    repo: str,
    changed_files: list[str],
) -> tuple[list[dict[str, object]], list[str]]:
    selected_repo = _normalize_repo(repo)
    adapter = _adapter_for_repo(selected_repo)
    if adapter is None:
        return [], [str(path).replace("\\", "/") for path in changed_files]
    routed: list[dict[str, object]] = []
    unmatched: list[str] = []
    for changed_file in changed_files:
        path = str(changed_file).replace("\\", "/")
        folded = path.casefold()
        hits = []
        for route in adapter.review_routes:
            prefix = str(route.get("prefix", "")).replace("\\", "/").casefold()
            doc = str(route.get("doc", ""))
            if prefix and doc and folded.startswith(prefix):
                hits.append({
                    "owner": route.get("owner") or prefix.rstrip("/"),
                    "doc": doc,
                })
        if not hits:
            unmatched.append(path)
            continue
        for hit in hits:
            doc = str(hit["doc"])
            doc_path = _knowledge_path(doc)
            routed.append({
                "owner": str(hit["owner"]),
                "path": doc_path,
                "relative_path": doc,
                "reason": f"changed file: {path}",
                "changed_file": path,
                "repo": selected_repo,
                "quick_map": _direct_quick_map(doc_path),
                "read_required": False,
            })
    return routed, unmatched


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


def _direct_mandatory_review_guides() -> list[str]:
    """Return required cross-owner review procedures, failing closed if absent."""
    return [
        _knowledge_path(relative_path)
        for relative_path in _DIRECT_MANDATORY_REVIEW_GUIDES
    ]


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


def _direct_quick_map(path: str, max_chars: int = 3500) -> tuple[str, str]:
    """Return the embedded Direct code map and its status, never the whole page.

    Status is ``ok`` / ``truncated`` / ``unavailable``. The last two both mean the
    host cannot rely on the excerpt alone.

    ``truncated`` is not cosmetic. The served `serving` page's section is 3754 chars
    against this 3500 cap, so 335 characters — including its request-contract rows —
    were being dropped with no marker, while the route said `read_required: False`.
    A partial map presented as whole is the same lie as a missing one, just harder
    to notice.
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    start = next(
        (
            index for index, line in enumerate(lines)
            if re.match(r"^##\s+.*Direct", line, re.IGNORECASE)
        ),
        None,
    )
    if start is None:
        return "", "unavailable"
    end = next(
        (
            index for index in range(start + 1, len(lines))
            if lines[index].startswith("## ")
        ),
        len(lines),
    )
    excerpt = "\n".join(lines[start:end]).strip()
    # the extract INCLUDES its own heading, so a section that is nothing but
    # `## Direct ...` is truthy while carrying no map at all
    if not "\n".join(excerpt.splitlines()[1:]).strip():
        return "", "unavailable"
    if len(excerpt) <= max_chars:
        return excerpt, "ok"
    # two passes so the marker reports the ACTUAL retained length: reserving room for
    # the note and rounding back to a line boundary both cut further than max_chars,
    # and a marker naming the cap would overstate what the host received
    probe = f"\n\n...[quick map truncated at {max_chars} of {len(excerpt)} chars]"
    kept = excerpt[:max_chars - len(probe)].rsplit("\n", 1)[0].rstrip()
    note = f"\n\n...[quick map truncated at {len(kept)} of {len(excerpt)} chars]"
    return kept + note, "truncated"


def _direct_route(owner: str, path: str, reason: str) -> dict:
    """One knowledge route, failing CLOSED when its quick map cannot be extracted.

    A rule page whose Direct heading is renamed used to yield ``quick_map: ""`` next to
    ``read_required: False`` — an empty map plus an instruction not to open the page,
    in the mode where the route *is* the deliverable. Degrading to "open it yourself"
    is a real fallback; handing over nothing and forbidding a look is not. The
    conformance test keeps the shipped tree honest; this keeps every other tree
    (``INFERMATRIX_KNOWLEDGE_DIR`` points wherever an operator says) honest too.
    """
    quick_map, status = _direct_quick_map(path)
    return {
        "owner": owner,
        "path": path,
        "reason": reason,
        "quick_map": quick_map,
        "quick_map_status": status,
        # a truncated map is as unreliable as a missing one for the rows that fell
        # off the end, so both send the host to the page
        "read_required": status != "ok",
    }


def _direct_execution_budget(changed_files: list[str], *,
                             knowledge_file_reads: int = 0) -> dict:
    """Bounded budget for one Direct review.

    `knowledge_file_reads` is normally 0 — the whole point of the embedded quick maps
    is that the host never opens a rule page. It is raised only by the count of routes
    whose quick map could not be extracted (bounded by the three-route cap): telling a
    host `read_required: True` while the budget forbids every knowledge read would be
    an unsatisfiable instruction, and unsatisfiable instructions get ignored wholesale.
    """
    normalized = [path.replace("\\", "/").casefold() for path in changed_files]
    docs_only = bool(normalized) and all(
        path.startswith(("docs/", "doc/", "recipes/"))
        or path.endswith((".md", ".mdx", ".rst", ".txt"))
        for path in normalized
    )
    return {
        "profile": "docs_only" if docs_only else "code",
        "knowledge_file_reads": knowledge_file_reads,
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
    changed_files: list[str] | None = None,
) -> dict:
    """Select bounded Direct knowledge routes from PR intent.

    Title/body select owners, and changed files report whether the frozen diff
    supports or contradicts that selection — they never silently *replace* a
    selection that reached the host.

    They do select as a LAST RESORT: when no route surviving the three-route cap
    matches an owner the changed files imply, scope-derived routes are added (the
    weakest description route is displaced if the cap is full). That case is never
    silent — ``status`` becomes ``scope_fallback``, ``selected_by`` becomes
    ``title_body+changed_files``, ``changed_files_role`` becomes
    ``selected_fallback_routes``, and each such route says ``changed files: ...`` in
    its reason. Handing the host nothing while holding the answer was the worse
    option: the owners were already computed and then discarded.
    """
    selected_repo = _normalize_repo(repo)
    changed_files = changed_files or []
    if not isinstance(changed_files, list) or any(
        not isinstance(path, str) for path in changed_files
    ):
        raise ValueError("changed_files must be a list of paths")

    # The repo guard runs FIRST. It used to sit below the empty-intent return, so a
    # description-less PR on an unsupported repo fell through to the generic path —
    # and once that path started deriving routes from changed files, it would have
    # served this repo's owner knowledge for a repo we do not serve.
    if selected_repo != "vllm-omni":
        # Adapter presence decides which non-default-repo case this is. Without the
        # gate, a repo we do not serve at all fell into the adapter path, whose
        # helper returns every changed file as "unmatched" when there is no
        # adapter — so garbage repos were reported as description_unrouted (a
        # served-repo status) instead of unsupported_exact_router, and the guard
        # this comment describes was silently lost for them.
        if _adapter_for_repo(selected_repo) is None:
            return {
                "status": "unsupported_exact_router",
                "selected_by": "title_body",
                "changed_files_role": "scope_validation_only",
                "routes": [],
                "scope_validation": [],
            }
        routes, unmatched = _adapter_changed_file_routes(
            selected_repo, changed_files)
        if routes or unmatched:
            return {
                "status": "ready" if routes else "description_unrouted",
                "selected_by": "adapter_changed_files",
                "changed_files_role": "route_and_scope_validation",
                "routes": routes[:3],
                "scope_validation": [{
                    "owner": route["owner"],
                    "changed_files": [route["changed_file"]],
                    "selected_from_description": False,
                } for route in routes],
                "unmatched_changed_files": unmatched,
                "unmatched_policy": (
                    "Unmatched changed paths remain reviewer-visible and must "
                    "not be treated as covered."),
            }
        return {
            "status": "unsupported_exact_router",
            "selected_by": "title_body",
            "changed_files_role": "scope_validation_only",
            "routes": [],
            "scope_validation": [],
        }

    intent = _route_text(f"{title}\n{body}")

    owner_routes: list[dict[str, object]] = []
    if intent:
        for route in _DIRECT_OWNER_ROUTES:
            matched = [
                signal for signal in route["signals"]
                if _signal_matches(intent, signal)
            ]
            if matched:
                owner_routes.append(_direct_route(
                    str(route["owner"]), _knowledge_path(str(route["path"])),
                    f"title/body: {', '.join(matched[:3])}"))

    model_routes: list[dict[str, object]] = []
    model_root = _KNOWLEDGE / "repos" / "vllm-omni" / "models"
    if intent:
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
                model_routes.append(_direct_route(
                    f"model:{model_dir.name}", str(rules.resolve()),
                    f"title/body model: {model_dir.name}"))

    routes = (model_routes + owner_routes)[:3]

    scope_hits: dict[str, list[str]] = {}
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
            scope_hits[str(route["owner"])] = hits
            scope_validation.append({
                "owner": route["owner"],
                "changed_files": hits,
                # reports the PRE-cap fact, which is what this field is for
                "selected_from_description": any(
                    item["owner"] == route["owner"] for item in owner_routes
                ),
            })

    # Fallback: the frozen diff already tells us which owners this PR touches, and
    # today that answer is computed and thrown away whenever the description picked
    # something else — or nothing. Measured over 60 merged PRs: 10 gain an owner they
    # previously dropped, 50 are unchanged.
    #
    # It does NOT rescue the separately-measured 6/60 that route to nothing at all:
    # those touch CODEOWNERS, docs/, recipes/, apps/ and tests/, which match no owner
    # prefix, so there is no owner to derive. Inventing one to move that number would
    # be worse than the gap. Those need a language-level default floor instead.
    #
    # Agreement is judged against the routes that SURVIVE the cap, not the pre-cap
    # owner list: an owner that matched the description but was displaced by
    # `[:3]` never reaches the host, so it must not suppress the fallback.
    surviving = {str(item["owner"]) for item in routes}
    fallback_used = False
    if scope_hits and not (surviving & set(scope_hits)):
        by_owner = {str(r["owner"]): r for r in _DIRECT_OWNER_ROUTES}
        # most changed files first, then owner name — the choice reflects evidence
        # rather than the declaration order of _DIRECT_OWNER_ROUTES
        candidates = sorted(scope_hits, key=lambda o: (-len(scope_hits[o]), o))
        for owner in candidates:
            if len(routes) >= 3:
                if fallback_used:
                    break
                routes.pop()  # displace the weakest description route, cap stays 3
            spec = by_owner[owner]
            routes.append(_direct_route(
                owner, _knowledge_path(str(spec["path"])),
                f"changed files: {', '.join(scope_hits[owner][:3])}"))
            fallback_used = True

    if fallback_used:
        status = "scope_fallback"
    elif routes:
        status = "ready"
    elif intent:
        status = "description_unrouted"
    else:
        status = "needs_pr_context"

    result: dict[str, object] = {
        "status": status,
        # both fields would be false statements once changed files pick a route
        "selected_by": "title_body+changed_files" if fallback_used else "title_body",
        "changed_files_role": ("selected_fallback_routes" if fallback_used
                               else "scope_validation_only"),
        "routes": routes,
        "scope_validation": scope_validation,
    }
    if status == "needs_pr_context":
        result["required"] = ["title", "body", "changed_files"]
    return result


def _direct_completion_result(
    subtraction_signal: str = "",
    subtraction: list[dict[str, str]] | None = None,
    minimality_proof: dict[str, str] | None = None,
    final_comment_count: int = 1,
    evidence_head_sha: str = "",
    existing_feedback_status: str = "not_applicable",
    finding_dispositions: list[dict[str, str]] | None = None,
) -> dict:
    """Mechanically gate Direct completion on subtraction classification.

    This deliberately checks structure, not whether the review evidence is
    true. A diff without a subtraction trigger can finish after explicitly
    declaring ``none``. Triggered diffs still need actionable subtraction or
    concrete evidence that the inspected scope is already minimal.
    ``evidence_head_sha`` forces an explicit declaration that every cited
    source file and validation result was read at the frozen head commit,
    not at whatever revision the local working tree happened to hold.
    """
    subtraction_signal = str(subtraction_signal).strip().casefold()
    subtraction = subtraction or []
    minimality_proof = minimality_proof or {}
    evidence_head_sha = str(evidence_head_sha).strip().casefold()
    existing_feedback_status = str(existing_feedback_status).strip().casefold()
    finding_dispositions = finding_dispositions or []
    missing: list[str] = []

    if final_comment_count != 1:
        missing.append("final_comment_count must be exactly 1")

    if subtraction_signal not in _SUBTRACTION_SIGNALS:
        missing.append("subtraction_signal must be 'none' or 'triggered'")

    if not _EVIDENCE_HEAD_SHA.fullmatch(evidence_head_sha):
        missing.append(
            "evidence_head_sha must be the frozen head commit SHA "
            "(7-40 hex characters) that every cited source file and "
            "validation result was read at"
        )

    if existing_feedback_status not in _FEEDBACK_STATUSES:
        missing.append(
            "existing_feedback_status must be 'checked', 'disabled', "
            "'unavailable', or 'not_applicable'"
        )

    malformed_dispositions: list[int] = []
    for index, item in enumerate(finding_dispositions):
        if not isinstance(item, dict):
            malformed_dispositions.append(index)
            continue
        anchor = str(item.get("anchor", "")).strip()
        disposition = str(item.get("disposition", "")).strip().casefold()
        existing_thread = str(item.get("existing_thread", "")).strip()
        head_recheck = str(item.get("head_recheck", "")).strip().casefold()
        needs_thread = disposition in {
            "duplicate",
            "extends_existing",
            "resolved_or_outdated",
        }
        if (
            ":" not in anchor
            or disposition not in _FINDING_DISPOSITIONS
            or (needs_thread and not existing_thread)
            or (
                disposition == "resolved_or_outdated"
                and head_recheck not in _RESOLVED_HEAD_RECHECKS
            )
        ):
            malformed_dispositions.append(index)
    if malformed_dispositions:
        missing.append(
            "each finding disposition needs a path:line anchor, a valid "
            "new/duplicate/extends_existing/resolved_or_outdated disposition, "
            "existing_thread for every non-new item, and head_recheck=fixed "
            "or still_affected for resolved_or_outdated items "
            f"(invalid indexes: {malformed_dispositions})"
        )
    if existing_feedback_status != "checked" and finding_dispositions:
        missing.append(
            "finding_dispositions require existing_feedback_status='checked'"
        )

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
        "evidence_head_sha": evidence_head_sha,
        "subtraction_signal": subtraction_signal,
        "subtraction_required": subtraction_signal == "triggered",
        "subtraction_items": len(subtraction),
        "minimality_proof": has_minimality_proof,
        "existing_feedback_status": existing_feedback_status,
        "finding_dispositions": len(finding_dispositions),
        "duplicate_findings_suppressed": sum(
            1
            for item in finding_dispositions
            if isinstance(item, dict)
            and (
                str(item.get("disposition", "")).strip().casefold()
                == "duplicate"
                or (
                    str(item.get("disposition", "")).strip().casefold()
                    == "resolved_or_outdated"
                    and str(item.get("head_recheck", "")).strip().casefold()
                    == "fixed"
                )
            )
        ),
        "resolved_or_outdated_still_affected": sum(
            1
            for item in finding_dispositions
            if isinstance(item, dict)
            and str(item.get("disposition", "")).strip().casefold()
            == "resolved_or_outdated"
            and str(item.get("head_recheck", "")).strip().casefold()
            == "still_affected"
        ),
        "missing": missing,
        "next_action": (
            "Return the single consolidated review comment with duplicate findings suppressed."
            if complete
            else "Classify the subtraction signal; only a triggered diff needs one bounded subtraction pass using the existing evidence packet."
        ),
    }


# ── public names ──────────────────────────────────────────────────────────────
# What `contract.py` re-exports. The underscored definitions above are the
# implementation and are kept only so `thin_mcp_server`'s existing call sites and
# tests keep working; new callers use these.
direct_knowledge_routes = _direct_knowledge_routes
direct_execution_budget = _direct_execution_budget
direct_completion_result = _direct_completion_result
direct_mandatory_review_guides = _direct_mandatory_review_guides
