# knowledge_service/curation.py — provider curation contract

<!-- verified-against: 2026-10-06 -->

`KnowledgeCurator.reviewed_rule_evidence(page_text, rule_id=..., source_reference=...)`
uses the canonical parser to verify one active, source-citing rule and returns
its exact UTF-8 section SHA256. `installed_knowledge_file(path)` reads canonical
`knowledge/repos/*.md` package resources from the installed provider, independent
of workspaces and environment overrides. Consumers can prove reviewed coverage
without copying domain parsing or importing provider-private modules.

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
