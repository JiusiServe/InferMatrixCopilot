# engine/planner.py — spec

`LOC ~116 · planning · refactor-status: ok`

## Responsibility
Resolve a `TaskSpec` (+ repo capabilities) to a runnable `Playbook` via
**reuse > adapt > generate**, with capability-gap handling.

## Functionality
Looks up a playbook (`store.find`); returns reuse (verbatim) / adapt (extra
params on non-locked → review) / generate (read-only kinds, fixed template);
raises `PlanningError` on locked-adapt, write-capable generate, or capability
gaps.

## Public contract
`Planner(store, registry)`; `resolve(spec, capabilities?) -> Resolution`;
`PlanningError`; `_GENERATE_TEMPLATES`.

## Invariants
- Reuse: `requires_review=False` when params ⊆ declared surface.
- Locked playbook refuses adaptation (raises).
- **C2**: generate is read-only-kinds-only and re-checks every step is
  `risk ∈ {read, report}` (raises otherwise).
- Capability gap (**§ARCH.8**): write-capable + unmet → raise "run repo_profile";
  read-only → generate; `capabilities=None` = v1 behavior.
- Tier comes from `spec.tier` — never invented.

## Scope — not here
Selection/parameterization only. No execution, no repo knowledge, no LLM,
no raw-tool composition (**A3**).

## Dependencies (allowed)
`playbooks/store`, `task_spec`, `engine/registry`.

## Extension points
New read-only kind needing generation → a `_GENERATE_TEMPLATES` entry of
read/report steps. Write-capable kinds must ship a vetted playbook.

## Tests
`test_planner_playbooks.py`, `test_capabilities.py`.

## Refactor notes
Small and clean; the three branches are the whole point — do not collapse them.
The capability-gap message text is user-facing guidance ("run repo_profile") —
keep it actionable. If generate ever needs LLM composition, it must still pass
the per-step risk re-check; never bypass C2 for flexibility.
