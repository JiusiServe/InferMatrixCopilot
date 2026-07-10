"""Review steps package: the conditional patch gate and the PR-review agent
step (`review.patch_gate`, `agent.review_diff`).

Importing this package imports `steps` for its `@step` registration side
effects. This was one 341-line module; the prompt data now lives in `prompts`,
the deterministic sweep/render helpers in `utils`, and the two handlers in
`steps`. The public contract below (spec: `engine/steps/review`) is re-exported
so existing `from ..steps.review import X` importers are unchanged.
"""

from __future__ import annotations

from . import steps  # noqa: F401  (side-effect: registers the two steps)
from .prompts import _REVIEW_LENSES  # noqa: F401
from .utils import _render_review_md, _sweep_targets  # noqa: F401

__all__ = ["_REVIEW_LENSES", "_render_review_md", "_sweep_targets"]
