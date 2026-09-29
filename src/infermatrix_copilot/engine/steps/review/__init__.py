"""Review steps package: the conditional patch gate and the PR-review agent
step (`review.patch_gate`, `agent.review_diff`).

Importing this package imports `patch_gate`, `quality`, and `steps` for
their `@step` registration side effects. The committed-range mutation gate
lives apart from the read-only review agent; the agent's bounded refinement
passes live in `refinement`. The public contract below (spec:
`engine/steps/review`) is re-exported for existing importers.
"""

from __future__ import annotations

from . import patch_gate, quality, steps  # noqa: F401  (side-effect: registers steps)
from .prompts import _REVIEW_LENSES  # noqa: F401
from .utils import _render_review_md, _sweep_targets  # noqa: F401

__all__ = ["_REVIEW_LENSES", "_render_review_md", "_sweep_targets"]
