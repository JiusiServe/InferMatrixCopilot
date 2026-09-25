# knowledge_service/ — provider curation components

<!-- verified-against: 2026-09-26 -->

The provider owns knowledge curation beneath the public SDK v1 facade.
`KnowledgeCurator` composes four domain components over one explicit work
checkout: `CatalogMixin` discovers contained owner rule pages and their
capacity; `PromptMixin` validates and bounds evidence and fences it as data;
`ProposalMixin` validates source/page/rule identity and binds accepted
proposals to page digests; `ApplyMixin` performs locked append-only writes,
fixed validators and byte-exact rollback. `common` contains shared syntax,
bounds, hashes, errors and lock capability.

No component imports a CLI/MCP transport or ReviewBot, calls a model, clones,
pushes, or publishes. The host owns evidence collection, model calls, retries,
local commits and proposal export. The public `sdk.v1.knowledge` module only
re-exports the curator and validator error. Existing proposal IDs, errors,
wire projections, validator order and rollback behavior are compatibility
contracts across the move.
