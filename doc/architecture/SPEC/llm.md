# llm.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~452 · engine substrate (transport) · refactor-status: ok`

## Responsibility
The provider-neutral LLM client wrapper. It supports Anthropic Messages and
OpenAI Chat Completions, including provider-specific Base URL overrides.

## Functionality
Wraps `messages.create`, exposes availability, normalizes replies into
`Reply`/`Block`, parses JSON out of model text.

## Public contract
`LLM(settings)` with `available`, `create(system, messages, tools?, model?,
max_tokens?, on_text?) -> Reply`; `Reply`, `Block`, `parse_json_reply`.

## Invariants
- `available` is false without a key/endpoint; callers must degrade
  (a `capability_gap`), not crash (**E2**).
- Untrusted content fencing is the caller's job, not here (**C7** lives in
  agent_runtime).
- **Per-tier endpoints.** `eco` and `performance` each resolve their own model,
  base URL and key, so a cheap tier can live on a different gateway entirely.
  A cheaper model still never widens permissions — `mode` is orthogonal to
  `tier` (see `task_spec.md`).
- **Fail-closed served-model guard**: if the endpoint reports serving a model
  other than the one requested, that is an error, not a silent substitution —
  an eval arm running on an unannounced model is a measurement lost.
- `cache_read_input_tokens` is captured for billing/cache analysis; callers and
  test fakes never touch SDK types, only the normalized `Reply`/`Block`.
- Harness backends do NOT come through here: they bypass `create()` entirely
  via `providers/harness_llm.py`, which raises if handed tools.

## Scope — not here
No prompts, no policy, no retries beyond transport. Not a place for
task/repo logic.

## Dependencies (allowed)
`anthropic` SDK; `openai` SDK; `config.py`.

## Extension points
New provider/endpoint → behind this wrapper's constructor; keep `Reply`/`Block`
stable so no caller changes.

## Tests
Provider selection and OpenAI tool translation are unit-tested; step/agent
tests use `ScriptedLLM`.

## Refactor notes
Keep the `Reply`/`Block` contract as the seam — callers must never see
provider-specific types.
