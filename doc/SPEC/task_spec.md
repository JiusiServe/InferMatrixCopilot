# task_spec.py — spec

`LOC ~70 · task layer, pure data · refactor-status: ok`

## Responsibility
Define `TaskSpec` (the structured product of intent parsing) and derive its
permission **tier** from the task kind.

## Functionality
Holds kind/repo/pr/issue/flags; computes `tier`, `read_only`,
`confirm_required`, and a human `describe()`.

## Public contract
`TaskSpec(kind, repo, pr?, issue?, report_only, post, params)`; properties
`tier`, `read_only`, `confirm_required`; `describe()`. Constants: `TaskKind`
(7 kinds), `READ_ONLY_KINDS`, `KIND_TIER`.

## Invariants
- **C1**: no settable tier field; `tier = KIND_TIER[kind]` — text can't widen it.
- `read_only` = `not post` for read-only kinds, else `report_only`;
  `confirm_required = not read_only`.

## Scope — not here
No parsing, no I/O, no execution, no repo knowledge. Pure data + derivation.

## Dependencies (allowed)
`pydantic` only.

## Extension points
New kind → add to `TaskKind` + `KIND_TIER` (+ `READ_ONLY_KINDS` if read-only).

## Tests
`test_intent_taskspec.py`.

## Refactor notes
Clean and minimal — the canonical example of "one responsibility". Do not add
behavior here; keep it a data+derivation module. It is the single source of
truth for C1, so any permission logic elsewhere is a smell.
