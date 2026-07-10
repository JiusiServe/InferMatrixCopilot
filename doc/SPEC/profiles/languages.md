# profiles/languages.py — spec

`LOC ~50 · edge (shared data) · refactor-status: ok`

## Responsibility
The single home for per-language rules (concision K2), previously triplicated.

## Public contract
`suffixes(language) -> tuple[str, ...]`; `symbol_re(language) -> Pattern | None`;
`sweep_re(language) -> (Pattern, Pattern) | None`.

## Functionality
Plain data maps (`_SUFFIXES`, `_SYMBOL_RE`, `_SWEEP_RE`) + tiny accessors.

## Invariants
- Unknown language returns empty/None so every consumer degrades honestly
  (file-level sweep only / empty module scan / "use grep").
- Pure data — no I/O, no state.

## Scope — not here
No scanning/rendering logic — the consumers (`review._sweep_targets`,
`establish.scan_modules`, `repo_map`) apply the rules.

## Dependencies (allowed)
stdlib `re` only. Must stay a leaf (`_ARCHITECTURE.md` §4) — no imports of
engine/profiles machinery.

## Tests
Exercised via the three consumers' tests
(`test_ci_and_repo_map.py`, `test_profile_steps.py`).

## Refactor notes
Adding a language = one row in each of the three maps. Keep it plain data; do
not grow it into a language-detection engine (detection stays in
`fingerprint_repo`). This is the deduplication target of K2 — do not re-inline
the rules into a consumer.
