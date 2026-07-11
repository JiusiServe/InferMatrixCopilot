# engine/steps/pr/ — spec

`LOC ~500 across 6 files · step library (PR) · refactor-status: split-applied (2026-07-11)`

## Responsibility
Guarded push, read-only PR fetch/gate, PR rebase, PR debug, gated review
posting. Formerly one 484-line module; now a package split by concern.

## Package layout (one concern per file)
- `__init__.py` — side-effect imports of the submodules (`@step`/`register_step`
  registration); re-exports `extract_signature`. No logic.
- `fetch.py` — read-only fetches: `pr.fetch_diff`, `pr.gate_check`.
- `rebase.py` — `pr.checkout_branch`, `pr.rebase_onto_base`, `pr.analyze_diff`,
  `agent.verify_module`.
- `debug.py` — `pr.fetch_ci_failures` (+ `_enrich_ci_logs`), `pr.group_failures`,
  `agent.debug_group`.
- `publish.py` — outward writes (risk=push): `ci.push`, `pr.post_review`.
- `utils.py` — the pure `extract_signature` (+ its regex).

## Steps (11)
`ci.push` (script/push); `pr.fetch_diff`, `pr.gate_check`, `pr.checkout_branch`,
`pr.analyze_diff`, `pr.fetch_ci_failures`, `pr.group_failures`
(deterministic/read); `pr.rebase_onto_base`, `agent.debug_group`
(agent/write_workspace); `agent.verify_module` (validation/read);
`pr.post_review` (script/push).

## Public contract (importable from `engine.steps.pr`)
`extract_signature` (re-exported from `utils`; used by tests).

## Invariants
- `ci.push` delegates all safety to `guard_push` (**C4**).
- `pr.checkout_branch` publishes the derived `PushPolicy` serialized (**B2**) —
  resume at push must not see the deny-all default.
- `pr.rebase_onto_base`: governed-agent conflict resolution or abort+escalate
  (workspace always restored).
- `pr.fetch_ci_failures` enriches logs via the profile-selected CI provider or
  records a `capability_gap` (**E2**); `pr.group_failures` groups by
  **normalized** signature.
- `pr.post_review` double-gated (**C5**).

## Scope — not here
No push authorization logic (that is `push`); no CI log fetching
mechanics (that is `ci/providers`); no agent governance (that is
`agent_runtime`).

## Dependencies (allowed)
`scopes`, `push`, `ci/*`, `adapters/base` (analyze), `engine/step`,
`.._common`, `..agent_runtime`.

## Tests
`test_pr_steps.py`, `test_push_and_steps.py`, `test_ci_and_repo_map.py`
(note: `test_ci_and_repo_map` monkeypatches `pr.debug._gh`, the submodule where
`pr.fetch_ci_failures` binds `gh`).

## Refactor notes
Split **applied**. The submodules share only `_common` helpers, so the split
creates no cross-import. The read/write axis is explicit: `fetch` is read-only,
`publish` holds both risk=push steps. K3/K4/K7 concision (require_repo/published/
from_state) is in place across the submodules. `_enrich_ci_logs` stays the thin
seam to `ci/providers`.
