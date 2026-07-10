# llm.py — spec

`LOC ~120 · engine substrate (transport) · refactor-status: ok`

## Responsibility
The Anthropic-SDK-compatible LLM client wrapper.

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

## Scope — not here
No prompts, no policy, no retries beyond transport. Not a place for
task/repo logic.

## Dependencies (allowed)
`anthropic` SDK; `config.py`.

## Extension points
New provider/endpoint → behind this wrapper's constructor; keep `Reply`/`Block`
stable so no caller changes.

## Tests
Faked via `ScriptedLLM` in step/agent tests (not unit-tested directly).

## Refactor notes
Thin and correct. If a second real provider is added, keep the `Reply`/`Block`
contract as the seam — callers must never see provider-specific types.
