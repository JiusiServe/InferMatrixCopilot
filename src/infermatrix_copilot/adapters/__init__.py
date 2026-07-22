"""Adapters subsystem: per-repo structure knowledge at the edge. Re-exports the
public surface — `RepoAdapter`/`AdapterRegistry`/`AdapterError`, the loaders and
writers (`load_adapter`, `update_manifest`), the Phase-0 bootstrap
(`fingerprint_repo`, `draft_adapter`), and `HIGH_RISK_SECTIONS` (the human-only
manifest sections) — so callers import from the package, not the module."""

from .base import (  # noqa: F401
    HIGH_RISK_SECTIONS,
    AdapterError,
    AdapterRegistry,
    RepoAdapter,
    draft_adapter,
    fingerprint_repo,
    load_adapter,
    update_manifest,
)
