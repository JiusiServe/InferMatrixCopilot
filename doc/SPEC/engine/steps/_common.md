# engine/steps/_common.py — spec

`LOC ~141 · step library infrastructure · refactor-status: ok`

## Responsibility
The step self-registration surface + cross-module helpers shared by step files.

## Functionality
`@step`/`register_step` decorator + `_COLLECTED` + `collected()`; helpers
`repo_path`, `task_spec`, `gh`, `git`, `gh_read_tools`, `post_step`.

## Public contract
`step(name, kind, risk, description, *, tool_scope?, patch_review_triggers?)`;
`register_step(StepSpec)`; `collected()`; the six helpers above.

## Invariants
- Duplicate step name → raise at import (**A4**).
- The **only** home for step-shared helpers — step modules import from here,
  never from each other (**A2**).
- Helpers are thin, side-effect-honest, repo-neutral.

## Scope — not here
No step handlers; no domain logic. Infrastructure + shared IO only.

## Dependencies (allowed)
`engine/step`; `...tools` (inside `gh_read_tools`), `...scopes` (types); stdlib.

## Extension points
A helper genuinely shared by ≥2 step files → add here. A helper used by one step
belongs in that step's file.

## Tests
Exercised via the step tests; `post_step`/`gh`/`git` patched in
`test_ci_and_repo_map.py` etc.

## Refactor notes
Watch for scope creep — if it accretes many single-user helpers, push them back
to their step. `gh`/`git`/`repo_path` are the true cross-cutting ones; keep the
monkeypatch seam (tests patch `steps.pr._gh`, i.e. the import alias) documented
so a future rename doesn't silently break patching.
