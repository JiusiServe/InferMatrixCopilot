# engine/pr_steps.py — spec

`LOC ~5 · compat shim · refactor-status: shim-to-retire`

## Responsibility
Backward-compat re-export of `extract_signature` from `engine.steps.pr`.

## Public contract
`extract_signature`.

## Invariants
Pure re-export; no logic.

## Importers to migrate before deleting
`test_pr_steps.py` imports `extract_signature`. (The `_gh` monkeypatch was
already retargeted to `engine.steps.pr` during the refactor.)

## Refactor notes
**Retire path (_CONCISION.md K5)**: point `test_pr_steps` at `from
omni_copilot.engine.steps.pr import extract_signature`, then delete file + spec.
