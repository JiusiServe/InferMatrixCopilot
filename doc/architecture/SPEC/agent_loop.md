# agent_loop.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~126 · engine (tool loop) · refactor-status: ok`

## Responsibility
The minimal tool-use loop, ToolScope-constrained and RunTrace-audited.

## Functionality
`run_agent` iterates: LLM call → collect tool_uses → `tools.dispatch` each →
feed results back; on budget exhaustion, force a final tool-free answer.

## Public contract
`run_agent(llm, *, system, prompt, scope, trace?, model?, max_iters,
extra_tools?) -> AgentOutcome`; `AgentOutcome`.

## Invariants
- The loop only ever sees tools its scope allows (via `tool_definitions_for`).
- Every call goes through `tools.dispatch` (**C3**).
- Budget exhaustion forces a final answer, not a discarded investigation.
- **The "FINAL ROUND" nudge must be appended AFTER the tool_result blocks.**
  Placing it between a `tool_use` and its `tool_result` violates the
  adjacency contract and fails the whole request with a 400. Pinned by
  `test_agent_loop.py::test_final_round_nudge_follows_tool_results`.
- This loop runs for `api` backends only; harness backends own their own loop
  and are delegated a whole step (`providers/base.md`).

## Scope — not here
No planning/step semantics; no output-contract coercion (that is
`agent_runtime`); no prompt construction beyond passing through.

## Dependencies (allowed)
`llm`, `run_trace`, `scopes`, `tools`.

## Extension points
None expected — it is the raw substrate `agent_runtime` builds on.

## Tests
`test_agent_loop.py`.

## Refactor notes
Correctly minimal. Keep it prompt-agnostic and contract-agnostic — all
governance/structure belongs one level up in `agent_runtime`. If the split of
`agent_runtime` happens, this file stays as-is (it is already the "loop" layer).
