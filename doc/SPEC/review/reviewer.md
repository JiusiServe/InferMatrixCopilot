# review/reviewer.py — spec

`LOC ~89 · review (verdict) · refactor-status: ok`

## Responsibility
The read-only patch/plan review verdict.

## Public contract
`run_patch_review(llm, diff_text, summary, fired_rules, model) -> verdict`;
`run_plan_review(llm, playbook_doc, task, model) -> verdict`.

## Invariants (**C6**)
- Returns `unavailable` without a reviewer LLM (a missing reviewer does not
  silently approve).
- Unparseable reviewer output degrades to `revise`.
- Anything but `lgtm`/`pass` is not-passing.

## Scope — not here
Not the review *step* (that is `engine/steps/review.py`); no trigger logic; no
diff building.

## Dependencies (allowed)
`llm`; the review prompt lives here.

## Tests
`test_review.py`.

## Refactor notes
Fail-closed is the invariant — never add a path where a missing/failed reviewer
returns passing. If plan and patch review diverge more, split into two files;
today they share the same fail-closed shape and belong together.
