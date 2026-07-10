"""Step — the engine's minimal governable execution unit (design §3.X).

A Step is one stable engineering action with declared risk and failure
semantics. Tools live below (inside steps); Playbooks above (graphs of steps).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Literal, Optional, TYPE_CHECKING

from ..run_trace import RunTrace

if TYPE_CHECKING:  # pragma: no cover
    from ..config import Settings
    from ..llm import LLM


class FailureKind(str, enum.Enum):
    RETRYABLE = "retryable"        # transient; executor retries bounded
    REPLAN = "replan"              # plan no longer valid; back to planner
    TEST_FAILURE = "test_failure"  # verification failed
    BLOCKED = "blocked"            # environment/permission blocks progress
    FORBIDDEN = "forbidden"        # step refused by policy (push guard, scope)
    ESCALATE = "escalate"          # needs a human decision


@dataclass
class StepResult:
    ok: bool
    failure: FailureKind | None = None
    summary: str = ""
    outputs: dict = field(default_factory=dict)
    changed_files: list[str] = field(default_factory=list)


@dataclass
class StepContext:
    """Everything a step handler may touch, injected by the executor."""

    settings: "Settings"
    state: dict                      # shared mutable run state
    params: dict                     # this step instance's params (from playbook)
    run_dir: Path
    trace: RunTrace
    llm: Optional["LLM"] = None
    item: Any = None                 # current foreach item, if any


Risk = Literal["read", "write_workspace", "push", "knowledge", "report"]
Kind = Literal["deterministic", "script", "agent", "validation", "report"]


@dataclass(frozen=True)
class StepSpec:
    name: str                        # e.g. "workspace.guard_clean"
    kind: Kind                       # descriptive; `agent` ⇒ governed runtime
    risk: Risk                       # enforced: planner bars write/push in generate
    handler: Callable[[StepContext], Awaitable[StepResult]]
    description: str = ""
