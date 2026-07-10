# review/diff_summary.py — spec

`LOC ~62 · review (always-on stage) · refactor-status: ok`

## Responsibility
The cheap, always-on first stage of patch review.

## Public contract
`build_diff_summary(repo, base_ref, primary_files, trace) -> DiffSummary`
(changed files, insertions/deletions, out-of-scope files, full-file writes,
tests run, push requested).

## Invariants
- Deterministic; no LLM.
- Reads git diff + RunTrace events (`out_of_scope_edit`, `full_file_write`,
  `test_run`, `push_requested`) to build the summary.

## Scope — not here
No trigger decisions (that is `triggers`), no verdict (that is `reviewer`).

## Dependencies (allowed)
`run_trace`; stdlib `subprocess`/`fnmatch`.

## Tests
`test_review.py`.

## Refactor notes
Clean single stage. Keep it cheap (no LLM) — it runs on every gate; the LLM only
runs when this summary trips a trigger.
