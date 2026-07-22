"""Executor — runs a Playbook's step graph with task-agnostic guarantees:
per-step checkpoint/resume, bounded retries, typed failure routing, RunTrace,
and escalation on BLOCKED/ESCALATE.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .step import FailureKind, StepContext, StepResult
from .registry import StepRegistry

if TYPE_CHECKING:  # pragma: no cover
    from ..config import Settings
    from ..llm import LLM
    from ..notify import Notifier
    from ..playbooks.store import Playbook
    from ..run_trace import RunTrace


@dataclass
class RunOutcome:
    """The result of running a whole playbook: a terminal `status` ("done" once
    every step passed, else "failed" or "blocked"), the per-step `step_results`
    keyed by playbook-step id, and a `blocked_reason` explaining an early halt."""

    status: str  # "done" | "failed" | "blocked"
    step_results: dict[str, StepResult] = field(default_factory=dict)
    blocked_reason: str = ""


class Executor:
    """Runs a Playbook's step graph with task-agnostic guarantees: per-step
    checkpoint/resume (progress.json), bounded retries, typed failure routing,
    RunTrace recording, and escalation on BLOCKED/ESCALATE/FORBIDDEN."""

    def __init__(
        self,
        registry: StepRegistry,
        settings: "Settings",
        *,
        run_dir: Path,
        trace: "RunTrace",
        llm: Optional["LLM"] = None,
        notifier: Optional["Notifier"] = None,
    ):
        """Wire the executor to its `registry` (step lookups), `settings`
        (retry bounds, post gates), the `run_dir` where progress.json is
        checkpointed, the `trace` sink, and optional `llm`/`notifier` handed to
        each step's context and used for escalation."""
        self.registry = registry
        self.settings = settings
        self.run_dir = Path(run_dir)
        self.trace = trace
        self.llm = llm
        self.notifier = notifier
        self.progress_file = self.run_dir / "progress.json"

    # -- checkpoint / resume ------------------------------------------------
    def _load_progress(self) -> dict:
        """Read the run's checkpoint (a `{"completed": {step_id: ...}}` map) from
        progress.json, or the empty checkpoint when this is a fresh run."""
        if self.progress_file.exists():
            return json.loads(self.progress_file.read_text(encoding="utf-8"))
        return {"completed": {}}

    def _save_progress(self, progress: dict) -> None:
        """Persist the checkpoint to progress.json (creating run_dir), so a later
        resume skips completed steps. `default=str` tolerates non-JSON values."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file.write_text(json.dumps(progress, indent=2, default=str))

    # -- execution ------------------------------------------------------------
    async def run(self, playbook: "Playbook", state: dict) -> RunOutcome:
        """Execute `playbook`'s steps in order against shared `state`, returning a
        RunOutcome. Each step is: gated by its `when:` condition (an unknown key
        blocks rather than silently skips), short-circuited if already in the
        checkpoint (its published `state_updates` are replayed so resume is
        faithful), otherwise fanned out over `foreach` items, merged, traced, and
        checkpointed on success. A BLOCKED/ESCALATE/FORBIDDEN failure notifies and
        halts as "blocked"; any other failure halts as "failed"."""
        progress = self._load_progress()
        outcome = RunOutcome(status="done")
        state.setdefault("playbook", playbook.name)
        # Run-scoped params (CLI `--task-param`, or intent-derived) reach every
        # step. Without this a step's `ctx.params.get(...)` only ever saw the
        # playbook's own step params, so `--task-param limit=5` was silently
        # dropped and issue.fetch kept its default of 20.
        task_params = (state.get("task_spec") or {}).get("params") or {}

        for pstep in playbook.steps:
            if pstep.when:
                try:
                    applies = _eval_when(pstep.when, state)
                except KeyError as exc:
                    outcome.status = "blocked"
                    outcome.blocked_reason = (
                        f"step '{pstep.id}': unknown `when:` key {exc} — "
                        "conditions may only reference TaskSpec fields or "
                        "state keys published by earlier steps")
                    return outcome
                if not applies:
                    outcome.step_results[pstep.id] = StepResult(
                        True, summary=f"skipped (when: {pstep.when})")
                    continue
            if pstep.id in progress["completed"]:
                cached = progress["completed"][pstep.id]
                cached_outputs = cached.get("outputs", {}) or {}
                # steps may publish JSON-simple state keys via outputs.state_updates
                # so resumed runs recover them without re-running the step
                state.update(cached_outputs.get("state_updates") or {})
                state.setdefault("outputs", {})[pstep.id] = cached_outputs
                outcome.step_results[pstep.id] = StepResult(
                    ok=True, summary=cached.get("summary", "(resumed)"),
                    outputs=cached_outputs,
                )
                continue

            spec = self.registry.get(pstep.step)
            items = state.get(pstep.foreach, [None]) if pstep.foreach else [None]
            if pstep.foreach and not isinstance(items, list):
                items = [items]

            _t0 = time.monotonic()
            # A playbook's own step params are authored invariants — several are
            # safety-bearing (`force_push`, `pre_push`) — so they override the
            # run-scoped ones rather than the other way round.
            step_params = {**task_params, **pstep.params}
            results = await asyncio.gather(
                *(self._run_step(spec, step_params, state, item) for item in items)
            )
            result = _merge(results)
            outcome.step_results[pstep.id] = result
            self.trace.record(
                "step_result", step=pstep.id, spec=spec.name, ok=result.ok,
                failure=result.failure.value if result.failure else None,
                summary=result.summary,
                dur_s=round(time.monotonic() - _t0, 2),  # labeled phase timing
            )

            if result.ok:
                progress["completed"][pstep.id] = {
                    "summary": result.summary, "outputs": result.outputs,
                }
                self._save_progress(progress)
                state.update((result.outputs or {}).get("state_updates") or {})
                state.setdefault("outputs", {})[pstep.id] = result.outputs
                continue

            # -- typed failure routing --
            if result.failure in (FailureKind.BLOCKED, FailureKind.ESCALATE,
                                  FailureKind.FORBIDDEN):
                reason = f"step '{pstep.id}' ({spec.name}): {result.summary}"
                if self.notifier is not None:
                    extra = result.outputs.get("escalation_summary") or {}
                    self.notifier.escalate(
                        reason=reason, phase=pstep.id, severity="blocked",
                        state_summary={"playbook": playbook.name, **extra},
                        artifacts=[str(self.progress_file),
                                   *result.outputs.get("artifacts", [])],
                    )
                outcome.status = "blocked"
                outcome.blocked_reason = reason
                return outcome

            outcome.status = "failed"
            outcome.blocked_reason = f"step '{pstep.id}' failed: {result.summary}"
            return outcome

        return outcome

    async def _run_step(self, spec, params: dict, state: dict, item) -> StepResult:
        """Invoke one step's handler inside a tracing span, retrying only on
        RETRYABLE up to `settings.max_step_retries`. Builds the StepContext from
        `params`, shared `state`, and the current foreach `item`; an unhandled
        exception is caught and converted to a BLOCKED StepResult so a handler bug
        never escapes as a raw exception. Returns the last StepResult produced."""
        from .. import tracing

        ctx = StepContext(
            settings=self.settings, state=state, params=params or {},
            run_dir=self.run_dir, trace=self.trace, llm=self.llm, item=item,
        )
        attempts = 1 + max(0, self.settings.max_step_retries)
        last: StepResult | None = None
        for attempt in range(1, attempts + 1):
            try:
                with tracing.span("step", step=spec.name, attempt=attempt):
                    last = await spec.handler(ctx)
            except Exception as exc:  # handler bug != typed failure
                last = StepResult(False, FailureKind.BLOCKED,
                                  f"unhandled error: {type(exc).__name__}: {exc}")
            if last.ok or last.failure is not FailureKind.RETRYABLE:
                return last
            self.trace.record("step_retry", spec=spec.name, attempt=attempt)
        return last  # exhausted retries


def _eval_when(when: str, state: dict) -> bool:
    """Evaluate a step condition: TaskSpec fields first (v1 semantics), then
    state keys published by earlier steps. Unknown keys raise KeyError instead
    of silently evaluating false (v2 P0 fix #3)."""
    spec = state.get("task_spec") or {}
    expr = when.strip()
    negate = expr.startswith("not ")
    key = expr[4:].strip() if negate else expr
    if key in spec:
        value = bool(spec.get(key))
    elif key in state:
        value = bool(state.get(key))
    else:
        raise KeyError(key)
    return (not value) if negate else value


def _merge(results: list[StepResult]) -> StepResult:
    """Merge foreach fan-out results: first failure wins, outputs keyed by index."""
    if len(results) == 1:
        return results[0]
    failed = [r for r in results if not r.ok]
    merged_outputs = {str(i): r.outputs for i, r in enumerate(results)}
    # lift state_updates to the top level (last writer wins per key) so the
    # executor's state.update / resume path sees fan-out publications too
    merged_updates: dict = {}
    for r in results:
        merged_updates.update((r.outputs or {}).get("state_updates") or {})
    if merged_updates:
        merged_outputs["state_updates"] = merged_updates
    changed = [f for r in results for f in r.changed_files]
    if failed:
        worst = failed[0]
        # surface the failing item's escalation material at the top level so
        # the notifier (which reads result.outputs directly) still sees it
        for key in ("escalation_summary", "artifacts"):
            if key in worst.outputs:
                merged_outputs[key] = worst.outputs[key]
        return StepResult(False, worst.failure,
                          f"{len(failed)}/{len(results)} items failed: {worst.summary}",
                          merged_outputs, changed)
    return StepResult(True, None, f"all {len(results)} items ok", merged_outputs, changed)
