"""Compat shim — the step library moved to `engine.steps` (see doc/CODE_TOUR.md
§5). Kept so existing imports (`register_builtin_steps` and the review helpers a
few tests reach for) keep working.
"""

from __future__ import annotations

from .steps import register_builtin_steps  # noqa: F401
from .steps.review import (  # noqa: F401
    _REVIEW_LENSES,
    _render_review_md,
    _sweep_targets,
)
