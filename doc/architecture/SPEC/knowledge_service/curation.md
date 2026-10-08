# knowledge_service/curation.py — provider curation contract

<!-- verified-against: 2026-10-09 -->

`KnowledgeCurator.reviewed_rule_evidence(page_text, rule_id=..., source_reference=...)`
uses the canonical parser to verify one active, source-citing rule and returns
its exact UTF-8 section SHA256. `installed_knowledge_file(path)` reads canonical
`knowledge/repos/*.md` package resources from the installed provider, independent
of workspaces and environment overrides. Consumers can prove reviewed coverage
without copying domain parsing or importing provider-private modules.

`KnowledgeCurator` delegates to provider-owned catalog, bounded evidence prompt,
proposal validation, append-only apply, fixed validator execution, and byte-exact
rollback for an explicit work checkout. `curate(batch, provider=..., command=...,
model=..., timeout_seconds=..., updated_on=..., generate=..., on_attempt=...)` also owns the
bounded generate/validate/apply attempt sequence. Backend arguments are trusted
host configuration, never fields selected by a candidate. It never clones a
repository, commits, pushes, or publishes a PR. The public
`sdk.v1.knowledge` module re-exports the class and `KnowledgeValidatorError`
without owning a second implementation.

The four components are module functions with explicit workspace, limit and
lock inputs, rather than mixin classes sharing attributes. The facade preserves
all public signatures and results, including schema and evidence helpers; its
successful append is still a local candidate rather than semantic admission.
See [knowledge lifecycle layers](../../knowledge-lifecycle.md).

Catalog targets are contained, non-symlink owner rule pages. Evidence is fenced
and byte-bounded. Proposal validation binds every accepted rule to its source,
page digest, and batch identity. Apply holds both an in-process mutex and an
interprocess file lock, rechecks page digests and rule ID uniqueness, and runs
the two fixed knowledge validators. Any failed validator restores the exact
original bytes of every target page.

Rule identity checks use the same raw heading parser as lifecycle operations;
the v1 path retains its existing fenced-text scan and append renderer. Locked
apply checks every declared and nested new ID across the entire candidate,
including proposals assembled from separately validated pages, before writing.

`curate` returns a dictionary with typed `validation` and `apply_result`
(or `None` when refused), `attempts` observations, and a terminal `error` string.
The existing separate validation/apply methods retain their typed return values.
An initial all-rejected proposal may be repaired once; an empty repair
cannot hide rejected rules. Validator failures permit at most two repairs only
after successful byte-exact rollback. Such repairs preserve all accepted rule
IDs, owner pages and source references. Repairs reuse the original bounded
evidence packet once and fence prior output/diagnostics as untrusted data.
Native intake uses the same bounded attempt driver with its own operations,
trace and repair policies.

The optional `on_attempt(observation)` diagnostic observer runs after validation
and before local apply. A validator refusal updates the same attempt ID after
rollback and before repair dispatch. Hosts may durably upsert these observations;
observer failures propagate without applying a candidate or dispatching a repair.
The callback owns no curation loop or publication authority.

The default model path uses the shared read-only JSON session with an ephemeral
regular-file-only knowledge snapshot and stripped publisher credentials. Codex
uses its schema and read-only sandbox; Cursor uses ask mode and may perform one
same-session formatting repair, with no sessionless retry. An embedded host may
instead supply `generate(prompt, schema)`. Every generation checks that the
source knowledge bytes remain unchanged; the host retains its broader checkout
permissions and restoration policy. The host owns evidence collection, model
budgets, diagnostic artifacts, local commits and proposal export. Curation
writes only the explicit checkout and never wheel resources.
