# engine/steps/profile.py — spec

`LOC ~387 · step library (profile pipeline) · refactor-status: split-candidate`

## Responsibility
The repo-profile establishment (Stages 0–1.5) + Stage-4 maintenance steps.

## Steps (8)
Establishment: `profile.fingerprint`, `profile.structure_scan`,
`profile.ingest_docs` (deterministic/knowledge), `agent.profile_repo`
(agent/knowledge). Stage-4: `profile.detect_drift` (deterministic/read),
`profile.decay_stale` (deterministic/knowledge), `agent.profile_consolidate`
(agent/knowledge), `profile.judge` (agent/read).

## Invariants
- `fingerprint` drafts a adapter at `status: draft` for unknown repos (human
  gate); `structure_scan` never overwrites declared modules.
- `agent.profile_repo` facts without evidence are rejected by the store;
  redundancy-filtered; overviews forbidden.
- `agent.profile_consolidate` is the ONLY rewrite/merge tier; the LLM's ops pass
  the store's stability gates (**D3/D4**).
- `profile.judge` never calls `apply_ops` (read-only, **D2**).
- No-LLM paths record a `capability_gap` and run only deterministic stages.

## Scope — not here
No store internals (that is `profiles/store`); no establishment helpers (those
are `profiles/establish`/`consolidate`).

## Dependencies (allowed)
`adapters/base`, `profiles/*`, `engine/step`, `._common`, `..agent_runtime`.

## Tests
`test_profile_steps.py`, `test_p3_machinery.py`.

## Refactor notes
Two lifecycles in one file. **Suggested split**: `steps/profile_establish.py`
(fingerprint/structure_scan/ingest_docs/profile_repo) and
`steps/profile_maintain.py` (detect_drift/decay_stale/consolidate/judge). They
share only `_adapter_from_state` (→ `_common` or a tiny `profiles` helper) and
the store — no cross-import. Guidance prompt constants could move beside the
review prompts under a `steps/*_prompts.py` convention.

## Concision — **K3** (biggest boilerplate collapse here)
This file has the densest guard repetition: **7** `_adapter_from_state` +
`isinstance(..., StepResult)` guards, **6** `ProfileStore(adapter.profile_dir)`
constructions, **3** no-LLM `capability_gap` blocks. Replace with `_common`
helpers `adapter_or_result`/`@needs_adapter`, `store_for(adapter)`,
`no_llm_gap(...)`. Expect ~25–35 LOC saved in this file alone. Preserve: each
step's name/behavior, the store's gates (D3/D4), and the `capability_gap`
events (E2). Do NOT let the helper hide the read-only-ness of `profile.judge`.
