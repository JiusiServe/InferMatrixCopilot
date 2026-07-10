# engine/steps/__init__.py — spec

`LOC ~31 · step library aggregation · refactor-status: ok`

## Responsibility
Import every step module for its registration side effects and expose
`register_builtin_steps`.

## Functionality
Imports `_common` + all 8 domain modules (running their `@step`/`register_step`
decorators, which fill `_common._COLLECTED`); `register_builtin_steps` flushes
the collection into a `StepRegistry`.

## Public contract
`register_builtin_steps(registry) -> registry`.

## Invariants
- Importing the package registers all steps exactly once (module cache);
  `register_builtin_steps` is idempotent per fresh registry (**A4**).
- The import list is the authoritative set of step modules — a new step module
  must be added here to be discovered.

## Scope — not here
No step logic, no registration policy beyond flushing.

## Dependencies (allowed)
`engine/registry`, `._common`, the 8 step modules.

## Extension points
New step domain module → add it to the side-effect import list.

## Tests
Exercised by every `register_builtin_steps(StepRegistry())` call (smoke: 38
steps).

## Refactor notes
Consider auto-discovery (iterate the package) to drop the manual import list —
but explicit imports are grep-able and fail loudly on typos, so the current
form is acceptable. If kept manual, this list + `_COLLECTED` is the single
source of "which steps exist".
