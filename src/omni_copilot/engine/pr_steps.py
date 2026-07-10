"""Compat shim — PR steps moved to `engine.steps.pr` (see doc/CODE_TOUR.md §5)."""

from __future__ import annotations

from .steps.pr import extract_signature  # noqa: F401
