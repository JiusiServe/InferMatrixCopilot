"""Profiles subsystem: the curated per-repo knowledge layer and its typed write
surface. Re-exports `ProfileStore`/`ProfileError` plus the two op allow-lists
(`RUN_OPS` additive per-run, `CONSOLIDATE_OPS` also rewrite/merge/stale) so the
tier gate is imported from the package, not the module."""

from .store import ProfileError, ProfileStore, RUN_OPS, CONSOLIDATE_OPS  # noqa: F401
