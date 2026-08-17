# thin_mcp_server.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~806 · the DEFAULT MCP: Direct routing + Strict entry · refactor-status: oversized`

## Responsibility
The MCP façade the installer actually registers: serve Direct-mode knowledge
routing with zero models, and bridge to Strict when asked.

## Functionality
Seven tools: `review` (branches on `mode`), `validate_direct_review`,
`get_review_status` / `get_review_result` (forwarded to `CopilotMCP`),
`update_knowledge`, `doc_search`, `doc_read`.

## Public contract
The seven tools above; `build_mcp(...)`; `main()`.

## Invariants (**C1**, **C2**, **D1**)
- **Direct runs NO model in this server.** It returns knowledge routes and a
  governance contract; the host's own model does the reading. The execution
  spine does not participate.
- **Governance is data, because the server cannot police the host.** "How to
  review" is encoded as structured fields travelling with the return value:
  ≤3 routes with embedded `quick_map` (3.5k cap), a hard `execution_budget`,
  a checklist.
- **`validate_direct_review` checks STRUCTURE, not evidence truth**: exactly
  one final comment, `subtraction_signal` consistency (`none` carries no
  evidence; `triggered` needs a subtraction item or minimality proof), and an
  `evidence_head_sha` proving the review read the pinned commit. It cannot and
  does not verify that cited evidence is real — claiming otherwise would be
  worse than not claiming it.
- **Routing never silently substitutes.** `title`/`body` select owners;
  `changed_files` normally only scope-validate. They select only as a LAST
  RESORT (when no surviving route matches an owner the files imply), and that
  case is explicit: `status="scope_fallback"`,
  `selected_by="title_body+changed_files"`, and each such route says why.
- **The repo guard runs FIRST.** An unsupported repo returns
  `unsupported_exact_router` before any route derivation — otherwise a
  description-less PR on a foreign repo would be served this repo's owner
  knowledge.
- `_knowledge_path` prevents escaping the knowledge root; `_guard` converts
  exceptions into `{"error": ...}` values rather than protocol faults.
- **Strict never starts doomed runs**: the Strict branch consults
  `strict_readiness` first and returns the missing items instead.
- `update_knowledge` returns only the contribution entry point — it is **not**
  `imupdate`'s release auditor.

## Scope — not here
No model calls in the Direct path; no Strict background machinery
(`mcp_server.py`); no policy definition (`mcp_policy.py`).

## Dependencies (allowed)
stdlib + `mcp` extra + `.adapters` + `.config` + `.intent.resolve_repo_alias` +
`.knowledge_docs` + `.mcp_policy` + `.mcp_server`.

## Tests
`test_thin_mcp_server.py`, `test_thin_mcp.py`, `test_imreview_output_contract.py`.

## Refactor notes
At ~806 LOC this is the largest module in the package; the Direct routing
helpers (`_direct_*`) are a coherent ~350-line unit and the obvious split if it
grows again. Keep the "server runs no model" property when splitting — it is
the product promise of Direct mode.
