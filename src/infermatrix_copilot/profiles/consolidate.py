"""Stage-4 profile maintenance (doc/DESIGN.md §V2.3.3): scheduled, gated
consolidation — the ONLY tier allowed to rewrite/merge — plus deterministic
staleness decay and drift detection. Mirrors the personal agent's weekly
pass: per-interaction writes stay additive because continuous LLM rewriting
measurably corrupts memory.
"""

from __future__ import annotations

import time
from pathlib import Path

from ..adapters.base import RepoAdapter
from .store import ProfileStore


def decay_stale(store: ProfileStore, *, days: int) -> list[str]:
    """Facts unconfirmed past the window flip to stale (excluded from every
    consumption channel, kept for audit — dormancy, never deletion)."""
    cutoff = time.time() - days * 86_400
    ops = []
    for fact in store.active():
        try:
            confirmed = time.mktime(time.strptime(fact.last_confirmed, "%Y-%m-%d"))
        except (ValueError, OverflowError):
            continue
        if confirmed < cutoff:
            ops.append({"op": "mark_stale", "id": fact.id})
    if ops:
        store.apply_ops(ops, tier="consolidate", actor="decay")
    return [op["id"] for op in ops]


def detect_drift(adapter: RepoAdapter, store: ProfileStore) -> list[str]:
    """Deterministic drift signals that should trigger a refresh proposal:
    declared module paths that no longer exist, and facts joined to modules
    the adapter no longer declares. Findings are REPORTS — nothing is
    auto-fixed here; the refresh re-runs the affected Stage-1 agent."""
    findings: list[str] = []
    repo = Path(adapter.repo_path) if adapter.repo_path else None
    if repo is not None and repo.exists():
        for module, spec in adapter.modules.items():
            for pattern in (spec or {}).get("local_paths", []):
                if not (repo / pattern.rstrip("*").rstrip("/")).exists():
                    findings.append(f"module '{module}': declared path "
                                    f"'{pattern}' no longer exists")
    known = set(adapter.modules) | {"repo-wide"}
    for fact in store.active():
        if fact.module not in known:
            findings.append(f"fact '{fact.id}': joined to unknown module "
                            f"'{fact.module}'")
    return findings
