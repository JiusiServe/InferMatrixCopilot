# providers/harness_llm.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~66 · LLM-shaped adapter over a harness (TOOL-LESS only) · refactor-status: ok`

## Responsibility
Let existing `llm.LLM` call sites keep working under a harness backend, for
tool-less calls only.

## Functionality
Wraps a `HarnessTransport` behind the `LLM` shape so callers that hold an
`LLM` (intent classification, ensemble reducer/merge, output repair, chat)
become one-shot CLI invocations under a harness backend.

## Public contract
`HarnessLLM` (`available`, `for_target`, `for_member`, `create`).

## Invariants (**C1**, **B1**)
- **Any call passing tools raises.** Agent steps must route through
  `run_session` — the harness owns its loop — and a loud error here is the
  guard against silently running a **second, ungoverned tool loop** alongside
  the vendor's. This is the single reason the module exists in this shape.
- Call sites are unchanged: `create()` keeps its signature, so no caller needs
  to know which backend is active.
- `for_member` is the MoA seam (a mixture member riding a harness inside an
  api-backed run).

## Scope — not here
No agent-step delegation (that is `run_session`); no tool bridging.

## Dependencies (allowed)
`.base` + `..llm` types.

## Tests
`test_providers.py`.

## Refactor notes
Resist adding a tools path "for convenience" — it would reintroduce exactly the
ungoverned second loop this class exists to prevent.
