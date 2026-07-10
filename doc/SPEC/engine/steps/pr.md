# engine/steps/pr.py — spec

`LOC ~493 · step library (PR) · refactor-status: split-candidate`

## Responsibility
Guarded push, read-only PR fetch/gate, PR rebase, PR debug, gated review
posting.

## Steps (11)
`ci.push` (script/push); `pr.fetch_diff`, `pr.gate_check`, `pr.checkout_branch`,
`pr.analyze_diff`, `pr.fetch_ci_failures`, `pr.group_failures`
(deterministic/read); `pr.rebase_onto_base`, `agent.debug_group`
(agent/write_workspace); `agent.verify_module` (validation/read);
`pr.post_review` (script/push).

## Public contract (re-exported by the `pr_steps` shim)
`extract_signature`.

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
`scopes`, `push`, `ci/*`, `plugins/base` (analyze), `engine/step`,
`._common`, `..agent_runtime`.

## Tests
`test_pr_steps.py`, `test_push_and_steps.py`, `test_ci_and_repo_map.py`.

## Refactor notes
Largest step file; three loosely-related flows share helpers. **Suggested
split** once it grows further: `steps/pr_rebase.py` (checkout / rebase_onto_base
/ analyze_diff / verify_module), `steps/pr_debug.py` (fetch_ci / enrich / group
/ debug_group + `extract_signature`), and keep `ci.push`/`pr.fetch_diff`/
`pr.gate_check`/`pr.post_review` in `pr.py`. They only share `_common` helpers,
so the split creates no cross-import. `_enrich_ci_logs` is the seam to
`ci/providers` — keep it thin.

## Concision — **K3/K4/K7** (do before any split)
Several repo-guard sites (K3 `require_repo`), verbose `state_updates` literals
(K4 `published(...)`), and the `pr.fetch_diff`/`pr.gate_check`/
`pr.fetch_ci_failures` "injected in state" early-returns (K7 `from_state`) can
collapse to single calls. `agent.verify_module`'s no-LLM block is a K3
`no_llm_gap` site. Do these first — the file may shrink enough that the
cohesion split above becomes optional. Preserve: B2 (PushPolicy still published
serialized), C4, C5, E2.
