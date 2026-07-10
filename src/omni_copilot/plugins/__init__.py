"""Plugins subsystem: per-repo structure knowledge at the edge. Re-exports the
public surface — `RepoPlugin`/`PluginRegistry`/`PluginError`, the loaders and
writers (`load_plugin`, `update_manifest`), the Phase-0 bootstrap
(`fingerprint_repo`, `draft_plugin`), and `HIGH_RISK_SECTIONS` (the human-only
manifest sections) — so callers import from the package, not the module."""

from .base import (  # noqa: F401
    HIGH_RISK_SECTIONS,
    PluginError,
    PluginRegistry,
    RepoPlugin,
    draft_plugin,
    fingerprint_repo,
    load_plugin,
    update_manifest,
)
