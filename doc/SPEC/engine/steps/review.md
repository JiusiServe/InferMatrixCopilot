# engine/steps/review/ — spec

`LOC ~350 across 4 files · step library (review) · refactor-status: split-applied (2026-07-10)`

## Responsibility
The conditional patch gate + the PR-review agent step and its repo-neutral
prompt system. Formerly one 341-line module; now a package that separates the
eval-tuned prompt data from the handlers and the deterministic helpers.

## Package layout (one concern per file)
- `__init__.py` — imports `steps` for `@step` registration side effects;
  re-exports the public contract (below). No logic.
- `prompts.py` — eval-derived prompt data: `_REVIEW_SYSTEM`, `_REVIEW_LENSES`,
  `_REVIEW_MERGE`. ~120 lines of text kept out of the control flow.
- `utils.py` — deterministic, LLM-free helpers: `_sweep_targets`,
  `_render_review_md`, `_SEVERITY_ORDER`.
- `steps.py` — the two `@step` handlers: `review.patch_gate` (validation/read),
  `agent.review_diff` (agent/read).

## Public contract (importable from `engine.steps.review`)
`_REVIEW_LENSES`, `_render_review_md`, `_sweep_targets` — re-exported from the
package `__init__` so the pre-split import paths are unchanged.

## Invariants
- Patch gate: cheap summary always, LLM review only on a trigger; fail-closed
  (**C6**); high-risk modules from the adapter, settings fallback (**A5**).
- Review: domain checklist extends from the profile's `review.md`;
  `_sweep_targets` keyed on `repo.language`, degrades honestly; verdict
  coherence (any ≥minor comment ⇒ REQUEST CHANGES); deterministic
  severity-ordered comment cap.
- Prompts are repo-neutral (**A5**).

## Scope — not here
No agent-runtime governance (that is `agent_runtime`); no adapter/profile writes.

## Dependencies (allowed)
`review/*`, `engine/step`, `.._common`, `..agent_runtime`, `profiles/languages`.

## Tests
`test_review_step.py`, `test_agent_ensemble.py`,
`test_profile_steps.py::test_review_guidance_from_profile`.

## Concision — **K2** (shared language rules, applied)
`_sweep_targets` consumes `profiles/languages.py::sweep_re` — one of the three
former copies of "per-language rules" (also `profiles/establish`, `repo_map`),
now collapsed to that single source. Unknown-language honest degradation
(file-level sweep only) is preserved.
