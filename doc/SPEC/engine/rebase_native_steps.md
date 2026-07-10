# engine/rebase_native_steps.py — spec

`LOC ~8 · compat shim · refactor-status: shim-to-retire`

## Responsibility
Backward-compat re-export of `_RUNTIME` (the same dict object) from
`engine.steps.rebase_native`, so test fixtures can clear it between runs.

## Public contract
`_RUNTIME`.

## Invariants
Pure re-export; the re-exported object is the SAME dict (so `.clear()` on either
name affects the one runtime).

## Importers to migrate before deleting
`test/conftest.py` and `test_rebase_native.py` clear `_RUNTIME` via
`from omni_copilot.engine import rebase_native_steps`.

## Refactor notes
**Retire path (_CONCISION.md K5)**: point those fixtures at
`from omni_copilot.engine.steps import rebase_native` and clear
`rebase_native._RUNTIME`, then delete file + spec. Keep the "same object"
guarantee until then — a `_RUNTIME = {}` reassignment anywhere would break the
clear-between-runs contract.
