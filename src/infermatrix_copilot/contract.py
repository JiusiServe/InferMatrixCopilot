"""The public cross-repo contract surface.

Everything a *consumer* of this copilot — a review bot, or any other host — is
allowed to import lives here, and nothing else is supported. The rule exists
because the alternative already caused version incidents: a downstream consumer
reaches into `thin_mcp_server` for four `_direct_*` privates through
`importlib`, so a rename inside a server module breaks a different repository
at runtime with no signal at build time.

Two things this module owns:

* **Versioning and the capability handshake.** A bot's preflight can ask what
  this copilot supports instead of discovering it from a failure.

* **The structured review result.** `get_review_result` used to return paged
  `RUN_REPORT.md` text, so a machine consumer had to scrape Markdown for the
  verdict and the findings — which meant a prose edit could silently change
  what a bot posted. `build_review_result` reads the facts from where the run
  already persisted them, and returns them typed.

Dependency direction: this module imports the copilot's data layers
(`run_status`, `run_trace`) and MUST NOT import either MCP server module. The
servers import *down* into this one. `test_contract.py` pins that.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import run_status as rs
from .direct_routing import (
    direct_completion_result,
    direct_execution_budget,
    direct_knowledge_routes,
    direct_mandatory_review_guides,
)
from .run_trace import RunTrace

__all__ = [
    "COMMENT_FIELDS",
    "DIRECT_API_VERSION",
    "STRICT_API_VERSION",
    "build_review_result",
    "capabilities",
    "direct_completion_result",
    "direct_execution_budget",
    "direct_knowledge_routes",
    "direct_mandatory_review_guides",
    "sanitize_comments",
    "unknown_run_result",
]

# Bumped when the shape below changes in a way a consumer must notice.
STRICT_API_VERSION = "1.0.0"
DIRECT_API_VERSION = "1.0.0"

# The only comment keys that cross the boundary. A review comment accumulates
# internal bookkeeping on real runs (`_verified`, `_anchor_unverified`,
# `corroborated_by`); publishing those would leak pipeline internals into a bot's
# output and freeze them into a contract nobody meant to make. Allow-list, so a
# new internal key is excluded by default rather than by remembering to.
COMMENT_FIELDS: frozenset[str] = frozenset({
    "file", "line", "severity", "comment", "evidence", "suggestion",
})

# Trace events the assembler surfaces as diagnostics.
_DIAGNOSTIC_EVENTS = ("review_plan", "capability_gap", "expected_head_mismatch",
                      "anchor_resolution", "diff_fallback")


def capabilities(*, max_strict_workers: int = 1,
                 supports_file_locking: bool = True) -> dict[str, Any]:
    """What this copilot can do, for a consumer's preflight.

    `max_strict_workers` is reported, not assumed: the MCP server drains its
    queue with a single worker, so a bot that fans out Strict requests should
    know they serialize rather than infer concurrency that does not exist."""
    return {
        "direct_api_version": DIRECT_API_VERSION,
        "strict_api_version": STRICT_API_VERSION,
        "supports_expected_head": True,
        "supports_structured_result": True,
        "supports_post_false": True,
        "supports_file_locking": bool(supports_file_locking),
        "max_strict_workers": int(max_strict_workers),
    }


def _read_json(path: Path) -> dict:
    """Parse `path`, or `{}` — a run that died early legitimately lacks these."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _state_updates(run_dir: Path) -> dict:
    """Every `state_updates` key published by a completed step, merged in step
    order — the same reconstruction `--resume` performs."""
    progress = _read_json(run_dir / "progress.json")
    merged: dict[str, Any] = {}
    for entry in (progress.get("completed") or {}).values():
        if isinstance(entry, dict):
            updates = (entry.get("outputs") or {}).get("state_updates")
            if isinstance(updates, dict):
                merged.update(updates)
    return merged


def sanitize_comments(comments: Any) -> list[dict]:
    """Project review comments onto `COMMENT_FIELDS`, dropping everything else."""
    out: list[dict] = []
    for c in comments if isinstance(comments, list) else []:
        if isinstance(c, dict):
            out.append({k: v for k, v in c.items() if k in COMMENT_FIELDS})
    return out


def build_review_result(run_dir: Path | str) -> dict[str, Any]:
    """The machine-readable result of one review run.

    Reads only what the run already persisted, so it works for a finished run,
    a running one, and one that died before the review step — which returns
    state plus diagnostics rather than raising. A caller polling an unknown id
    is handled one level up (`state: "unknown"`), so that "lost" and "still
    running" stay distinguishable."""
    run_dir = Path(run_dir)
    status = rs.read_status(run_dir) or {}
    updates = _state_updates(run_dir)
    trace = RunTrace(run_dir / "run_trace.jsonl")

    diagnostics: dict[str, Any] = {}
    for name in _DIAGNOSTIC_EVENTS:
        events = [{k: v for k, v in e.items() if k not in ("ts", "kind")}
                  for e in trace.events(name)]
        if events:
            diagnostics[name] = events

    metrics = _read_json(run_dir / "metrics.json")
    cost = metrics.get("cost") or {}
    if cost:
        diagnostics["cost"] = {
            "usd": cost.get("usd"), "minutes": cost.get("minutes"),
            "input_tokens": cost.get("input_tokens"),
            "output_tokens": cost.get("output_tokens"),
        }

    # A stale head is the one outcome a caller must not have to infer from
    # prose: it means "your snapshot is gone", not "the review found nothing".
    mismatch = (diagnostics.get("expected_head_mismatch") or [None])[0]

    return {
        "contract_version": STRICT_API_VERSION,
        "run_id": status.get("run_id") or run_dir.name,
        "state": status.get("state") or "unknown",
        "note": status.get("note") or "",
        "reviewed_head_sha": str(updates.get("pr_head_sha") or ""),
        "verdict": str(updates.get("review_verdict") or ""),
        "summary_markdown": str(updates.get("review_summary") or ""),
        "comments": sanitize_comments(updates.get("review_comments")),
        "stale": bool(mismatch),
        "expected_head_sha": str((mismatch or {}).get("expected") or ""),
        "actual_head_sha": str((mismatch or {}).get("actual") or ""),
        "diagnostics": diagnostics,
    }


def unknown_run_result(run_id: str) -> dict[str, Any]:
    """The result for an id this server has never heard of.

    Explicit rather than an exception so a bot holding an id it can no longer
    match — a lost response, a restarted server — can tell "lost" from "still
    running" and decide whether to retry."""
    return {"contract_version": STRICT_API_VERSION, "run_id": run_id,
            "state": "unknown", "note": "", "reviewed_head_sha": "",
            "verdict": "", "summary_markdown": "", "comments": [],
            "stale": False, "expected_head_sha": "", "actual_head_sha": "",
            "diagnostics": {}}
