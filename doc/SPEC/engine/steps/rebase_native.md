# engine/steps/rebase_native.py — spec

`LOC ~397 · step library (candidate native rebase) · refactor-status: ok`

## Responsibility
The candidate native decomposition of the nightly rebase, importing the parent
package's own phase wrappers + `node_rebase_module`.

## Steps (9)
`rebase.prelude`, `rebase.phase1..phase5`, `rebase.phase2_prepare`,
`rebase.module_rebase`, `rebase.phase2_finalize`, `rebase.compare_with_locked`.

## Public contract (importable from `engine.steps.rebase_native`)
`_RUNTIME` (per-process memoized parent runtime; test fixtures clear it).

## Invariants
- Invisible to the planner (candidate playbook `repo-rebase-native` only).
- Phase-4 push is behind the copilot push guard; env export is traced
  (`env_exported`).
- Delegates to the parent's functions — does not reimplement phases.
- Names the parent package (allowed repo literals, leak-capped at 6).

## Scope — not here
No promotion logic; no rebase reimplementation. Wrapper only.

## Dependencies (allowed)
`rebase/monitor`, `plugins/base` (wave cross-check), `engine/step`, `._common`;
the external `agent.*` package (lazy imports, ImportError → BLOCKED).

## Tests
`test_rebase_native.py`.

## Refactor notes
By design coupled to the parent package — the 6 repo literals and the parent
imports are the delegation surface, not a smell. Registered imperatively
(mixed factory/direct handlers) — that is the sanctioned exception to `@step`.
Only touch when working the promotion path (candidate → active → locked).
