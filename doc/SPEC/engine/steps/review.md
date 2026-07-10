# engine/steps/review.py — spec

`LOC ~347 · step library (review) · refactor-status: split-candidate`

## Responsibility
The conditional patch gate + the PR-review agent step and its repo-neutral
prompt system.

## Steps
`review.patch_gate` (validation/read), `agent.review_diff` (agent/read).

## Public contract (re-exported by the `builtin_steps` shim)
`_REVIEW_LENSES`, `_render_review_md`, `_sweep_targets`.

## Invariants
- Patch gate: cheap summary always, LLM review only on a trigger; fail-closed
  (**C6**); high-risk modules from the plugin, settings fallback (**A5**).
- Review: domain checklist extends from the profile's `review.md`;
  `_sweep_targets` keyed on `repo.language`, degrades honestly; verdict
  coherence (any ≥minor comment ⇒ REQUEST CHANGES); deterministic
  severity-ordered comment cap.
- Prompts are repo-neutral (**A5**).

## Scope — not here
No agent-runtime governance (that is `agent_runtime`); no plugin/profile writes.

## Dependencies (allowed)
`review/*`, `scopes`, `engine/step`, `._common`, `..agent_runtime`.

## Tests
`test_review_step.py`, `test_agent_ensemble.py`,
`test_profile_steps.py::test_review_guidance_from_profile`.

## Refactor notes
Half the file is prompt constants (`_REVIEW_SYSTEM`, `_REVIEW_LENSES`,
`_REVIEW_MERGE`). **Suggested split**: move the prompt data to
`steps/review_prompts.py` (or a `.txt`/`.md` loaded at import), leaving the two
handlers + `_sweep_targets`/`_render_review_md` here. The eval-derived comments
on the lenses are rationale — keep them beside the lens data.

## Concision — **K2** (shared language rules)
`_sweep_targets`'s `line_rules` (per-language branch/index regexes) is one of
three copies of "per-language rules" (also in `profiles/establish` and
`profiles/repo_map`). Move the data to `profiles/languages.py` and consume it
here. Preserve: unknown-language honest degradation (file-level sweep only).
