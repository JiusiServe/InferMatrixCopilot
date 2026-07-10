# engine/registry.py — spec

`LOC ~31 · engine substrate · refactor-status: ok`

## Responsibility
`StepRegistry`: the name → `StepSpec` map — the single place a name string
resolves to a handler.

## Functionality
`register`/`get`/`__contains__`/`names`.

## Public contract
`StepRegistry` with the methods above.

## Invariants
- Duplicate registration raises; `get` on unknown raises with the registered set
  (fail loudly, never silent).

## Scope — not here
Storage/lookup only — no execution, no policy, no self-population (population is
`steps.register_builtin_steps`).

## Dependencies (allowed)
`engine/step`.

## Extension points
None needed; it is a container.

## Tests
Exercised via `register_builtin_steps` in most tests.

## Refactor notes
Minimal and correct. Do not add filtering/policy here — that belongs to the
planner (which selects) and the store (which validates references).
