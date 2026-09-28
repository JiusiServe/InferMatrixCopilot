# knowledge_service/ — provider curation components

<!-- verified-against: 2026-09-28 -->

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

Knowledge Ops API 2.0 sits beside the v1 curator and does not change it:
`lifecycle` parses rule pages (byte-exact) and their `kb:rule` footers,
`ops.apply_operations` applies typed add / edit_same_meaning / replace / retire
/ purge changes with their mechanical consequences, and `l1` is the
deterministic half of the quality gate (`check_tree`, `check_changeset`). The
three modules need only the standard library and PyYAML and import nothing else
from the package, so the kb-gate verifier bundle can vendor them.

`release_audit` loads a repository's release-audit plugin from its adapter
directory and runs it with a baseline generated for the audited SHA pair:
knowledge-document issues are enforced, adapter-baseline maintenance is
reported as reconciliation.

`signing` provides Ed25519 envelopes whose signature covers a purpose tag plus
the canonical JSON payload, so a signature made for one purpose (gate verdict,
outbox item, control record, hold list, publisher ack) never verifies for
another. It needs only `cryptography` and is vendored by the kb-gate verifier.
