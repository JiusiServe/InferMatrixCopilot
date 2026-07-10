# engine/builtin_steps.py — spec

`LOC ~13 · compat shim · refactor-status: shim-to-retire`

## Responsibility
Backward-compat re-export after the `engine/steps/` refactor.

## Functionality
Re-exports `register_builtin_steps` (from `engine.steps`) and the review helpers
`_REVIEW_LENSES`, `_render_review_md`, `_sweep_targets` (from
`engine.steps.review`).

## Public contract
`register_builtin_steps`, `_REVIEW_LENSES`, `_render_review_md`,
`_sweep_targets`.

## Invariants
- Pure re-export; no logic. 0 repo literals.

## Importers to migrate before deleting
Most tests import `register_builtin_steps` from here; `test_profile_steps` and
`test_agent_ensemble` import the review helpers from here.

## Refactor notes
**Retire path (_CONCISION.md K5)**: migrate importers to `from
omni_copilot.engine.steps import register_builtin_steps` and `from
omni_copilot.engine.steps.review import ...`, then delete this file + its spec.
Part of the ~26-LOC / 3-file shim removal.
