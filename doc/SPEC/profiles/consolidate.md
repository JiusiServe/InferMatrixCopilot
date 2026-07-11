# profiles/consolidate.py — spec

`LOC ~52 · profiles (Stage-4 helpers) · refactor-status: ok`

## Responsibility
Deterministic Stage-4 helpers: staleness decay + drift detection.

## Public contract
`decay_stale(store, days) -> stale ids`; `detect_drift(adapter, store) ->
findings`.

## Invariants
- `decay_stale` flips over-window active facts to `stale` (excluded, not
  deleted) via the store's `mark_stale` op (**D4**).
- `detect_drift` is **report-only** — declared module paths that vanished, facts
  joined to unknown modules; it never mutates.

## Scope — not here
Deterministic detection only — no LLM, no auto-fix (consolidation is the
`agent.profile_consolidate` step).

## Dependencies (allowed)
`adapters/base`, `profiles/store`; stdlib `time`.

## Tests
`test_p3_machinery.py`.

## Refactor notes
Small and pure. Keep `detect_drift` report-only — the "findings become refresh
proposals, never auto-fixes" rule is the whole point (**D2**).
