"""Vetted step library, assembled explicitly when a registry is requested.

Each module still keeps its step name, metadata and handler together with
`@step` / `register_step`. Importing this package alone is inert; only
`register_builtin_steps` loads the vetted modules and fills a `StepRegistry`.
This keeps application and SDK imports from loading every workflow effect.
"""

from __future__ import annotations

from importlib import import_module

from ..registry import StepRegistry
from . import _common

_BUILTIN_MODULES = (
    "workspace", "review", "report", "pr", "issue", "profile",
    "rebase_v3", "rebase_knowledge",
)


def register_builtin_steps(registry: StepRegistry) -> StepRegistry:
    """Load the vetted modules and install their collected specs into `registry`.

    Module imports are cached by Python, so repeated registry assembly uses
    the same step definitions without a second registration side effect.
    """
    for name in _BUILTIN_MODULES:
        import_module(f"{__name__}.{name}")
    for spec in _common.collected():
        registry.register(spec)
    return registry
