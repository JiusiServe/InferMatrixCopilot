"""Vetted step library, self-registering via the `@step` decorator.

Importing this package imports every step module for its registration side
effects (each `@step` / `register_step` records a `StepSpec`);
`register_builtin_steps` flushes the collected specs into a `StepRegistry`.
There is no central `add(StepSpec(...))` block to keep in sync — a step's name,
metadata and handler live together at its definition (see doc/CODE_TOUR.md §5).
"""

from __future__ import annotations

from ..registry import StepRegistry
from . import _common

# side-effect imports: each module registers its steps into the collection.
from . import (  # noqa: F401,E402
    workspace,
    rebase_ext,
    review,
    report,
    pr,
    issue,
    profile,
    rebase_native,
)


def register_builtin_steps(registry: StepRegistry) -> StepRegistry:
    for spec in _common.collected():
        registry.register(spec)
    return registry
