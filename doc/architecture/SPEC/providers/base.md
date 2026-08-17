# providers/base.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~161 · provider-layer contracts + subprocess env allowlist · refactor-status: ok`

## Responsibility
The contracts every provider implements, and the safety primitive that decides
what environment a vendor CLI subprocess inherits.

## Functionality
Defines the two provider kinds (`api` — stateless completions, our
`agent_loop` owns the tool loop; `harness` — a vendor agent that owns its own
loop, so the seam is a whole step), the request/usage dataclasses, the
`HarnessTransport` base with shared binary resolution, and `sanitized_env()`.

## Public contract
`ProviderSpec`, `AgentSessionRequest`, `SessionUsage`, `HarnessTransport`
(`cli_path`, `require_cli`, `auth_gap`, `run_session`, `complete`),
`sanitized_env()`, `flatten_messages()`.

## Invariants (**C1**, **C4**, **E2**)
- **The env is an allowlist, not a denylist** (`_ENV_KEEP` + `LC_`/`XDG_`
  prefixes). A vendor CLI must keep its subscription auth (HOME state) but must
  never inherit our model endpoints: on this class of machine an inherited
  `ANTHROPIC_BASE_URL` points at a gateway and would silently reroute the
  vendor's traffic. API keys, gh tokens and host markers like `CLAUDECODE` are
  dropped for the same reason.
- **Never fabricate cost.** Harnesses report usage unevenly; absent numbers
  stay `0` and `cost_usd` stays `None`, so metrics record source
  `"subscription"` rather than inventing USD.
- **The seam is a whole step.** `run_session` receives the SAME prompt bundle
  `run_agent` would (contract `system` + rendered dispatch context), so a
  harness run is the same review, not a different one.
- `flatten_messages` is for TOOL-LESS conversations only — the caller
  guarantees it. Flattening a tool conversation would silently drop tool
  results.
- `auth_gap()` returning `None` means "unknown or fine", never "verified good":
  a transport without a cheap check must let the run fail loudly rather than
  assert readiness it did not test.

## Scope — not here
No vendor-specific invocation (each transport); no registry table; no
credential resolution for `api` (that is `Settings`).

## Dependencies (allowed)
stdlib + `..scopes.ToolScope`. It is a leaf contract module.

## Extension points
New capability flags go in `ProviderSpec.capabilities`; new session bounds go
in `AgentSessionRequest`.

## Tests
`test_providers.py` (env allowlist, spec shape).

## Refactor notes
`sanitized_env()` is a safety primitive like `push.guard_push` and
`scopes` — keep it pure and dependency-free. Widening `_ENV_KEEP` is a security
decision, not a convenience one.
