# profiles/establish.py — spec

`LOC ~107 · profiles (Stage 0–1.5 helpers) · refactor-status: ok`

## Responsibility
Deterministic establishment helpers.

## Public contract
`fact_id`, `build_doc_corpus`, `is_redundant`, `extract_directives`,
`scan_modules`, `HUMAN_DOC_NAMES`, `LANGUAGE_SUFFIXES`.

## Invariants
- `is_redundant` (6-word shingle vs README+docs) drops any briefing line the
  repo's own docs already state (the ETH-study rule, **D5**).
- `scan_modules` deterministic, language-keyed, skips non-code dirs.
- `extract_directives` bounds line length (short imperative only).

## Scope — not here
Pure deterministic helpers — no LLM, no store writes, no step logic.

## Dependencies (allowed)
stdlib only.

## Tests
`test_profile_steps.py` (redundancy filter, module scan, directive extraction).

## Refactor notes
Pure functions — easy to test and reuse. The redundancy filter is the
load-bearing ETH-study defense; keep it deterministic. ## Concision — **K2** (shared language rules)
`LANGUAGE_SUFFIXES` (+ the language use in `scan_modules`) is one of three copies
of the per-language rule set (also `review._sweep_targets`, `repo_map`). Move the
data to a leaf `profiles/languages.py` and consume it here; keep it a plain data
map + tiny accessors. Preserve: unknown language → empty module scan.
