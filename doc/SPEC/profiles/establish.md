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
load-bearing ETH-study defense; keep it deterministic. Language extractors
(`LANGUAGE_SUFFIXES` + `scan_modules`) share the language-keying idea with
`review._sweep_targets` and `repo_map` — a future refactor could centralize the
"per-language rules" table, but only if it stays a plain data map.
