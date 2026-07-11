# memory/debug_memory.py — spec

`LOC ~106 · memory (failure→fix store) · refactor-status: ok`

## Responsibility
FTS5 store of failure→fix experience.

## Public contract
`DebugMemory(db_path)` with `search(query, k)` and a write method taking the
required fields.

## Invariants (**D1/D3**)
- A write must include repo/module/run_id/symptom/root_cause/fix_summary/files/
  verification/status.
- Retrieval is top-k-by-relevance, summary-first.
- Facts recorded freely; promotion to a skill is a separate gated act.

## Scope — not here
No per-repo namespacing (the agent runtime's `_ScopedKnowledge` applies that);
no LLM.

## Dependencies (allowed)
stdlib `sqlite3`.

## Tests
`test_memory.py`.

## Refactor notes
The write contract (required fields) is the D3 guarantee — enforce it at write
time, never accept a partial memory. Per-repo DB path is chosen by the caller
(`adapter.debug_memory_db`) — keep this class path-agnostic.
