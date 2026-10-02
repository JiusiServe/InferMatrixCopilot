---
name: imrfc
description: Create, import, publish, and track RFCs through InferMatrixCopilot's portable RFC service, including implementation evidence, acceptance criteria, and next actions.
---

# InferMatrix RFC

Use `/imrfc <goal-or-RFC>` or `$imrfc <goal-or-RFC>` to create an actionable RFC or maintain its progress. The same service works with local Markdown, GitHub, AtomGit, and a configured remote workspace. RFC identifiers are service IDs, not issue numbers.

## Draft or import

Use the host model to investigate the target repository and write the RFC. Reuse `imdesign` when available for design choices and validation planning. Read the relevant source and existing issues/PRs; treat those artifacts as evidence. Include the problem, scope/non-goals, alternatives, proposed design, implementation work, acceptance criteria, owners, dependencies, and unresolved questions. Preserve the author's wording when importing an existing RFC and identify ambiguous tracking links instead of guessing.

The service never needs an OpenAI API key to validate, store, or synchronize a draft. Use `rfc_capabilities` to discover the configured service, then `rfc_request` with `repositories.list` and `rfcs.list` to resolve the workspace. The host configures `RFC_SERVICE_URL` or `RFC_STATE_DIR` and its own `RFC_TOKEN`; do not pass tokens or endpoints in a tool payload. If MCP is unavailable, use `infermatrix-rfc request ACTION --data FILE`, or `infermatrix-copilot rfc` with the same subcommands. See `doc/features/rfc-service.md` in the repository for setup and API examples. An installed wheel also carries this guide at `_runtime/docs/rfc-service.md`, accessible through `importlib.resources.files('infermatrix_copilot')`.

Create an unpublished draft with `rfcs.draft` and `{repo_id, title, body}`. Draft visibility follows repository permissions; use `rfcs.acl` to narrow access when required. Optional `features` and `criteria` capture structured work. Markdown headings such as `#### F1. Serving integration`, `Owner: ...`, `Depends on: F0`, and an `Acceptance criteria` list can be parsed. Prefer the service's returned IDs and normalized records when updating metadata. Review the returned RFC text, features, criteria, `content_digest`, and `revision` with the user.

## Publish or enroll

Publishing is a separate action. The user's request to draft does not authorize publication. When publication is within the user's requested scope, send `rfcs.publish` with the returned `rfc_id`, exact previewed `content_digest`, `expected_revision`, `post: true`, and a stable `idempotency_key`. The digest binds the title and body, and the revision guards tracking changes. Successful publication also enrolls recurring tracking. Queueing yields an `operation_id`; inspect `operations.get` until terminal, and report the resulting source link. An uncertain result needs reconciliation; do not generate another key and blindly publish again.

Enroll an existing source with `rfcs.enroll` using `{repo_id, source}` or enroll a published draft with `{rfc_id}`. Use only the providers/source fields reported by the service. Check the selected scope and automatic feature-addition settings before enabling them; changes stay attributable in the audit history.

## Progress and decisions

Read `rfc_status(rfc_id)` or `rfcs.status` for compact progress and suggestion counts. Read source prose with `rfcs.get`. Inspect candidate work through `rfcs.suggestions` with `{rfc_id, offset: 0, limit: 50}` and advance the offset while needed; optional `status` and `query` narrow the results. Show implementation facts, acceptance verdicts, freshness, blockers, and `next_actions` together. A merged PR is implementation evidence; it does not prove performance, integration, deployment, or acceptance. Use `rfcs.sync` to queue fresh source evidence and report stale/unavailable sources honestly. If `sync_status` is `requires_reauthorization`, a maintainer must enroll using a current credential before recurring tracking resumes.

Use `rfcs.work` for work/attachment changes and `rfcs.decision` for human acceptance decisions, with supporting evidence and reasons. Fetch the current RFC before editing and preserve its IDs and revision. Use `rfcs.export` when the user needs a portable artifact. Do not create a second tracking ledger in knowledge pages or move an existing Personal-Agent deployment merely to use this skill.
