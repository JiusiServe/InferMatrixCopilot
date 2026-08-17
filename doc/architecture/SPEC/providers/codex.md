# providers/codex.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~197 · harness transport (ChatGPT subscription) · refactor-status: ok`

## Responsibility
Run a whole agent step through the `codex` CLI on ChatGPT subscription auth.

## Functionality
`codex exec` with MCP overrides pointing at the tool bridge, event-stream
parsing for the final text and usage, and an OS-level read-only sandbox as the
containment control.

## Public contract
`CodexTransport` (`auth_gap`, `run_session`, `complete`),
`spec = PROVIDERS["codex"]`.

## Invariants (**C1**, **C2**)
- **The sandbox is the control, not the tool list.** Codex cannot disable its
  native shell, so containment is `--sandbox read-only` at the OS level. Broad
  *reads* inside the sandbox are therefore possible and accepted; what the
  sandbox guarantees is that nothing is written.
- Bridged tool calls still pass `tools.dispatch`; the sandbox is defence in
  depth, not a replacement.
- `_tool_activity` is a best-effort activity log, explicitly **not an audit** —
  the sandbox is the enforcement point. Do not let callers treat it as one.
- `complete()` runs tool-less in an empty scratch cwd, so a one-shot call
  cannot reach the repo at all.
- `auth_gap()` reports the ChatGPT-login gap: this backend is offline-tested
  only (no login on the dev machine), and readiness must say so rather than
  imply verification.

## Scope — not here
No sandbox policy invention (the CLI flag is the contract); no usage
fabrication.

## Dependencies (allowed)
stdlib + `.base` + `..agent_loop.AgentOutcome` + `..llm` types.

## Tests
`test_provider_codex.py` (offline; the live path is unverified by design —
see the status note in `doc/features/provider-registry.md`).

## Refactor notes
Do not "improve" `_tool_activity` into an audit: `providers/audit.py` exists
for backends where no OS-level control is available, and conflating the two
would blur which control class is actually in force — a fact RUN_REPORT
discloses.
