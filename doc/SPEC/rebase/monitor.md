# rebase/monitor.py — spec

`LOC ~159 · edge (external pipeline monitor) · refactor-status: ok`

## Responsibility
Read/classify the parent orchestrator's state for the locked
`rebase.run_external` delegation.

## Public contract
`build_command`, `parse_parent_state`, `summarize_progress`, `diff_progress`,
`classify_failure`, `build_escalation`.

## Invariants
- Read-only toward the parent's `state.json`.
- Classifies exit code + state into a typed failure + escalation material.
- Stale-state aware — a prior run's `phase=done` must not mask this run's crash.
- Names the parent package/paths (allowed repo literals, leak-capped at 1).

## Scope — not here
Does not run or reimplement the rebase; no push logic; no notification (that is
`notify`).

## Dependencies (allowed)
stdlib `json`/`subprocess` only.

## Tests
`test_rebase_monitor.py`.

## Refactor notes
Cohesive monitoring/classification unit. The baseline-signature comparison here
is the known-weak spot the CI-normalize module was written to avoid inheriting —
if this monitor's classification is ever tightened, reuse `ci/normalize` rather
than re-implementing string compare.
