# knowledge_service/curation.py — provider curation contract

<!-- verified-against: 2026-09-26 -->

`KnowledgeCurator` composes provider-owned catalog, bounded evidence prompt,
proposal validation, append-only apply, fixed validator execution, and byte-exact
rollback for an explicit work checkout. It imports only SDK contract models and
standard-library services; it never imports a CLI/MCP transport, calls a model,
clones a repository, pushes, or publishes a PR. The public
`sdk.v1.knowledge` module re-exports the class and `KnowledgeValidatorError`
without owning a second implementation.

Catalog targets are contained, non-symlink owner rule pages. Evidence is fenced
and byte-bounded. Proposal validation binds every accepted rule to its source,
page digest, and batch identity. Apply holds both an in-process mutex and an
interprocess file lock, rechecks page digests and rule ID uniqueness, and runs
the two fixed knowledge validators. Any failed validator restores the exact
original bytes of every target page.

The host owns evidence collection, model calls, retries, local commits and
proposal export. Curation writes only the explicit checkout and never wheel
resources. Installed-wheel imports and temp-checkout apply/rollback tests must
remain valid.
