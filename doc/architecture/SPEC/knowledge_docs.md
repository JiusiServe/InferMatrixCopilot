# knowledge_docs.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~122 · read-only knowledge retrieval for the MCP surface · refactor-status: ok`

## Responsibility
Cross-platform, repo-scoped read access to the curated Markdown knowledge base
— the substrate under `doc_search`/`doc_read`.

## Public contract
`KnowledgeDocs` (search, read), `KnowledgeDocsError`.

## Invariants (**C1**, **D1**)
- **Scoped to a slice**: the general slice plus a single repo's slice. A path
  outside the knowledge root is refused (`KnowledgeDocsError`) — the
  path-escape guard.
- **Read-only.** There is no write surface here at all; knowledge writes go
  through the candidate/typed-op path elsewhere.
- Reads are **paginated** (24k per page) so a large page cannot blow up a host
  conversation.
- Search is deterministic word-overlap scoring — no model call.

## Scope — not here
No knowledge authoring, no candidate proposal, no repo-specific rules in code
(the tree is the data plane).

## Dependencies (allowed)
stdlib only.

## Tests
`test_knowledge_source.py`, `test_thin_mcp_server.py`.

## Refactor notes
Keep it model-free: this is the one knowledge reader shared by the Direct MCP
path and the tool bridge, and a model call here would put a second model inside
a "server runs no model" guarantee.
