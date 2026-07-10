# ci/normalize.py — spec

`LOC ~31 · edge (CI) · refactor-status: ok`

## Responsibility
Normalize a CI failure signature before grouping.

## Public contract
`normalize_signature(signature) -> str`.

## Invariants
- Strips run-varying noise (timestamps, hashes, addresses, tmp paths, line
  numbers, durations); keeps small literal numbers as signal.
- Deliberate non-inheritance of the parent monitor's exact-string-compare bug —
  the same failure across runs must collapse to one group.

## Scope — not here
String normalization only — no grouping (that is `pr.group_failures`), no log
fetching (that is `ci/providers`).

## Dependencies (allowed)
stdlib `re` only.

## Tests
`test_ci_and_repo_map.py`.

## Refactor notes
Tiny and pure — the normalization rules are the whole value. If false-merges
appear in practice, tune the regex table here (one place), not at call sites.
