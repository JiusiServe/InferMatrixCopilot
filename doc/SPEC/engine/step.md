# engine/step.py — spec

`LOC ~67 · engine base vocabulary · refactor-status: ok`

## Responsibility
The base execution vocabulary shared by the whole engine.

## Functionality
Defines the failure taxonomy, the step result/context/spec dataclasses, and the
`Kind`/`Risk` literal sets.

## Public contract
`FailureKind` (RETRYABLE, REPLAN, TEST_FAILURE, BLOCKED, FORBIDDEN, ESCALATE);
`StepResult(ok, failure?, summary, outputs, changed_files)`;
`StepContext(settings, state, params, run_dir, trace, llm?, item?)`;
`StepSpec(name, kind, risk, handler, description)`. `Kind ∈ {deterministic,
script, agent, validation, report}`; `Risk ∈ {read, write_workspace, push,
knowledge, report}`.

## Invariants
- Repo- and task-agnostic; `StepSpec` is frozen.
- The six `FailureKind`s are the complete routing vocabulary (**B1**).
- `risk` is enforced (planner C2); `kind` is descriptive (`agent` ⇒ governed
  runtime by convention). No decorative fields: a `StepSpec` field must be read
  by something (the `tool_scope`/`patch_review_triggers` fields were removed
  because nothing enforced them — scope/triggers are handler-local).

## Scope — not here
Types only — no behavior, no registry, no execution.

## Dependencies (allowed)
Only `run_trace` (**§ARCH.4.3**). Nothing task/repo-specific.

## Extension points
A new `Kind`/`Risk` value or `FailureKind` is a deliberate vocabulary change —
update the executor routing and `_CONSTRAINTS` together.

## Tests
Exercised everywhere; shape pinned implicitly.

## Refactor notes
Foundational — keep the dependency set at exactly {run_trace, scopes}. Adding an
import here would couple the whole engine to it. If `StepContext` grows more
optional fields, that's a signal a step is over-reaching, not that this file
needs restructuring.
