"""Step registry — planners compose registered steps only, never raw tools."""

from __future__ import annotations

from .step import StepSpec


class StepRegistry:
    def __init__(self) -> None:
        self._steps: dict[str, StepSpec] = {}

    def register(self, spec: StepSpec) -> StepSpec:
        if spec.name in self._steps:
            raise ValueError(f"step already registered: {spec.name}")
        self._steps[spec.name] = spec
        return spec

    def get(self, name: str) -> StepSpec:
        try:
            return self._steps[name]
        except KeyError:
            raise KeyError(f"unknown step: {name!r} (registered: {sorted(self._steps)})") from None

    def __contains__(self, name: str) -> bool:
        return name in self._steps

    def names(self) -> list[str]:
        return sorted(self._steps)
