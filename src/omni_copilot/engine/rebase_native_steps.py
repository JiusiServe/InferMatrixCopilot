"""Compat shim — native rebase steps moved to `engine.steps.rebase_native`
(see doc/CODE_TOUR.md §5). `_RUNTIME` is re-exported (same dict object) so the
test fixtures that clear it between runs keep working.
"""

from __future__ import annotations

from .steps.rebase_native import _RUNTIME  # noqa: F401
