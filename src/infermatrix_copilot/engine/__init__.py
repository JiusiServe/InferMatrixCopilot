"""Engine package: the task-agnostic execution core (Step → Registry → Executor,
with the Planner that composes steps into a run). Re-exports the public surface —
`FailureKind`, `StepContext`, `StepResult`, `StepSpec`, `StepRegistry`,
`Executor`, `RunOutcome` — so callers import from the package, not its modules."""

from .step import FailureKind, StepContext, StepResult, StepSpec  # noqa: F401
from .registry import StepRegistry  # noqa: F401
from .executor import Executor, RunOutcome  # noqa: F401
