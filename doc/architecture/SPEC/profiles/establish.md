# profiles/establish.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~107 · profiles (Stage 0–1.5 helpers) · refactor-status: ok`

## Responsibility
Deterministic establishment helpers.

## Public contract
`fact_id`, `build_doc_corpus`, `is_redundant`, `extract_directives`,
`scan_modules`, `HUMAN_DOC_NAMES`.

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
load-bearing ETH-study defense; keep it deterministic.

## Concision — **K2** (shared language rules) — DONE
This module used to own `LANGUAGE_SUFFIXES`, one of three copies of the
per-language rule set (with `review._sweep_targets` and `repo_map`). The data
now lives in the leaf `profiles/languages.py` behind small accessors
(`suffixes` / `symbol_re` / `sweep_re`) and is consumed from there; the symbol
is gone from this module's public contract. Preserved as designed: an unknown
language yields an empty module scan rather than a guess.
