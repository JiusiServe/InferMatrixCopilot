# engine/steps/workspace.py — spec

`LOC ~43 · step library · refactor-status: ok`

## Responsibility
Workspace precondition + cheap diff summary steps.

## Steps
`workspace.guard_clean` (deterministic/read), `analysis.diff_summary`
(deterministic/read).

## Invariants
- `guard_clean` refuses to start on a dirty tree (BLOCKED) — the precondition
  for any write-capable run.
- Both are deterministic — no LLM.

## Scope — not here
No mutation of the workspace; no repo knowledge.

## Dependencies (allowed)
`review/diff_summary`, `engine/step`, `._common`.

## Tests
`test_push_and_steps.py` (guard), diff-summary via review tests.

## Refactor notes
Trivial and correct. If more read-only "analysis" steps appear, they can share
this file.

## Concision — **K3**
`guard_clean`/`diff_summary` each repeat the `repo is None → BLOCKED` guard →
`require_repo(ctx)` (one of the 8 K3 sites).
