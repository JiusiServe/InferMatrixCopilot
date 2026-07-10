# profiles/store.py — spec

`LOC ~268 · profiles (curated layer) · refactor-status: ok`

## Responsibility
The curated fact store: typed patch ops as the only write surface, provenance/
stability gates, channel-typed rendering.

## Public contract
`ProfileStore(root)`; `apply_ops(ops, tier, actor) -> per-op reject reasons`;
`active(channel?, module?)`; `render_briefing(budget)`; `render_report()`.
`Fact`; `RUN_OPS`/`CONSOLIDATE_OPS`; `CHANNELS`, `KINDS`, `SOURCES`,
`STABLE_CONFIRMATIONS`, `BRIEFING_WORD_BUDGET`.

## Invariants
- Ops are the ONLY mutation path; malformed/forbidden ops rejected individually
  (never raise); wrong-tier ops rejected (**D4**).
- `add_fact` needs text + evidence; duplicate id = confirmation (**D3**).
- `rewrite_fact` never leaves a fact evidence-free; stable (≥3) facts may not
  drop cited evidence; superseded text → `history` (**D3**).
- `merge_facts` leaves a pointer stub (never deletes); `mark_stale` excludes but
  keeps for audit.
- `render_briefing` emits only active briefing-channel facts, most-confirmed
  first, under the hard word budget (**D5**).
- Every accepted op → `ops_log.jsonl`; `save()` re-renders `PROFILE_REPORT.md`.

## Scope — not here
No LLM, no repo scanning, no step logic.

## Dependencies (allowed)
`pyyaml`; stdlib.

## Tests
`test_profile_store.py`.

## Refactor notes
The reference implementation of D3/D4 — do not add a mutation path outside
`apply_ops`. Each `_op_*` is a small validator; keep them individually
rejectable. If op kinds grow, keep `RUN_OPS`/`CONSOLIDATE_OPS` as the tier
gate. This is the transplant of the personal-agent store — keep them
conceptually aligned.
