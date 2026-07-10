# engine/steps/rebase_ext.py — spec

`LOC ~101 · step library (delegation) · refactor-status: ok`

## Responsibility
`rebase.run_external` — monitored subprocess delegation to the locked 5-phase
orchestrator (wrap-don't-rewrite).

## Steps
`rebase.run_external` (script/write_workspace).

## Invariants
- Zero-regression: does NOT reimplement the pipeline.
- Streams parent `state.json` into RunTrace; stale-state guard prevents a prior
  run's `phase=done` masking a crash; failures classified into escalation
  material.
- Names the parent package (an allowed repo literal, leak-capped at 1).

## Scope — not here
No rebase logic of its own; no parsing beyond delegating to `rebase/monitor`.

## Dependencies (allowed)
`rebase/monitor`, `engine/step`, `._common`; stdlib asyncio/subprocess.

## Tests
`test_rebase_monitor.py` (the monitor it drives).

## Refactor notes
Acceptable. The one repo literal (`"vllm-omni-rebase-agent"`) is by-design
delegation text — do not templatize it prematurely; if a second external
orchestrator is ever wrapped, then extract the name to the plugin.
