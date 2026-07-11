# review/triggers.py — spec

`LOC ~50 · review (trigger rules) · refactor-status: ok`

## Responsibility
Decide when the LLM patch review fires.

## Public contract
`evaluate_triggers(summary, settings, *, touched_modules, pre_push,
knowledge_edit, high_risk_modules?) -> fired[]`; `ALL_RULES` (7).

## Invariants
- Seven rules: `out_of_scope_edits, high_risk_modules, large_diff,
  tests_unavailable, full_file_fallback, before_push, knowledge_edit`.
- High-risk modules come from the caller (adapter), settings only as fallback
  (**A5**).

## Scope — not here
No diff building (that is `diff_summary`), no LLM call (that is the step, which
calls `reviewer` when a trigger fires).

## Dependencies (allowed)
`config`, `review/diff_summary`.

## Tests
`test_review.py`.

## Refactor notes
The rule set is the contract — adding/removing a trigger changes the safety
posture (**C6**) and must be a deliberate, documented change. Keep it a pure
function of (summary, settings, caller flags).
