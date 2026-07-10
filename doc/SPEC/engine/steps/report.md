# engine/steps/report.py — spec

`LOC ~24 · step library · refactor-status: ok`

## Responsibility
`report.final_summary` — write `RUN_REPORT.md` from accumulated step outputs.

## Steps
`report.final_summary` (report/report).

## Invariants
- Pure output; no failure paths (always ok).
- Reads `ctx.state["outputs"]`; writes only the run dir.

## Scope — not here
No analysis, no repo knowledge, no side effects beyond the report file.

## Dependencies (allowed)
`engine/step`, `._common`.

## Tests
Exercised in playbook end-to-end tests.

## Refactor notes
Trivial. If richer reporting is wanted, keep it additive and side-effect-free.
