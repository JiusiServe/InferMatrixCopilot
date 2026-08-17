# engine/steps/review/ — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~900 across 6 files · step library (review) · refactor-status: ok`

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
- `anchor.py` — snippet-anchored comment placement (added 2026-08).
- `repo_tools.py` — the read-only change-archaeology tool set (added 2026-08).

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
- **Ask for a quote, not a line number** (`anchor.py`). Models get line numbers
  wrong often enough that the finding was demoted at publish time; the fix is a
  different question — have the model quote the code and compute the position
  in program code. The validator still runs last, so "never post a wrong
  anchor" is unchanged; what changes is that a finding whose ONLY defect was
  the number keeps its inline position instead of being demoted into the body.
- **Verdict calibration**: only *verified* blocker/major findings block; minor
  degrades to COMMENT, and a self-declared-uncertain finding never blocks.
- **An escalation carrying comments is salvaged as a successful
  REQUEST CHANGES** — finding defects IS a successful review.
- **Archaeology tools are recall machinery, not convenience** (`repo_tools.py`).
  Wave-2 forensics measured that the judge-decisive moves the baseline made and
  our passes could not were all one-command capabilities the read-only toolset
  simply lacked (`git diff --stat base..HEAD` proving a requested removal was
  absent; reading a file at the merge base; `git show` / `git log -S`).
- A **coverage-driven second round** is seeded from the run's own coverage
  holes; the **verification ledger** promotes residue the run already wrote
  down — forensics found misses were often recorded approvingly rather than
  raised.

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
