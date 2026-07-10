"""Step registry — planners compose registered steps only, never raw tools."""

from __future__ import annotations

from .step import StepSpec


class StepRegistry:
    """The name → StepSpec table a planner draws from: only registered steps may
    appear in a plan, so raw tools never enter a pipeline. Names are unique."""

    def __init__(self) -> None:
        """Start with an empty step table."""
        self._steps: dict[str, StepSpec] = {}

    def register(self, spec: StepSpec) -> StepSpec:
        """Record `spec` under its name, rejecting a duplicate name with
        ValueError (fail-closed against two steps claiming one name). Returns the
        spec so registration can be chained/decorated."""
        if spec.name in self._steps:
            raise ValueError(f"step already registered: {spec.name}")
        self._steps[spec.name] = spec
        return spec

    def get(self, name: str) -> StepSpec:
        """Return the StepSpec for `name`, or raise KeyError listing the
        registered names — an unknown step is a plan/config error, never silent."""
        try:
            return self._steps[name]
        except KeyError:
            raise KeyError(f"unknown step: {name!r} (registered: {sorted(self._steps)})") from None

    def __contains__(self, name: str) -> bool:
        """True if a step named `name` is registered."""
        return name in self._steps

    def names(self) -> list[str]:
        """The registered step names, sorted."""
        return sorted(self._steps)
