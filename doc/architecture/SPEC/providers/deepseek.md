# providers/deepseek.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~502 · harness transport (dsh, API-keyed) · refactor-status: oversized`

## Responsibility
Run a whole agent step on DeepSeek's own agent harness (`dsh`) through its
Python SDK — the backend that breaks two of the registry's harness assumptions,
both deliberately and both disclosed.

## Functionality
Drives `deepseek-harness-sdk` (itself a subprocess SDK launching the bundled
`dsh-jsonrpc-agent` over JSON-RPC/stdio), generating a per-session composition
so the sandbox mode can be pinned per scope.

## Public contract
`DeepSeekHarnessTransport` (`cli_path`, `require_cli`, `auth_gap`,
`run_session`, `complete`), `spec = PROVIDERS["deepseek"]`.

## Invariants (**C1**, **C2**, **E2**)
- **It is API-keyed, not subscription-authed.** `base.md` states harnesses hold
  their own auth and `Settings.tier_target` returns an empty key for harnesses
  precisely for that reason. dsh is the exception: it needs a DeepSeek
  credential, handed over `DeepSeekHarnessConfig.api_key`. For
  cursor/claude-code/codex, injecting a key would be a **bug**; here it is the
  only way the harness runs at all. The registry marks this `api_keyed`.
- **It CANNOT use our tool bridge — a measured fact, not a choice.** The
  bundled runtime compiles in 122 plugins and `@deepseek-ai/dsh-mcp-client` is
  not among them (verified by scanning the executable). Sessions therefore run
  on the harness's native `bash` + `str_replace_editor`, and our scoped tools —
  including the archaeology set — are unreachable as named tools.
  A `review.mcp_tool_bridge` `capability_gap` is traced on every session handed
  a bridge spec it could not honour, and the outcome reports `mcp_bridged=False`.
  **The registry must NOT declare `mcp_tools` for this provider** (it did until
  2026-08-17; nothing branched on it, so the false claim only ever misled
  readers).
- **An arm must never be labelled "tools bridged" when it ran on native bash.**
  This campaign has already measured three arms that were not the configuration
  their label claimed.
- **The sandbox mode is pinned, never inherited.** Upstream minimal ships
  `mode: danger-full-access` and its own README says to use it only against a
  disposable checkout. This machine is shared and `.env` holds live
  credentials, so the generated composition pins the mode to the session's
  scope.
- **The step cap is 6× our in-process budget** (`_STEP_CAP_FACTOR`), not 1:1:
  measured healthy lenses took ~40 steps against a budget of 14, so a 1:1 cap
  would truncate normal sessions; 6× still stops a runaway an order of
  magnitude short of the 558 steps observed.
- `_assert_plugins_bundled` fails loudly if the runtime's plugin set stops
  matching what the composition assumes.

## Scope — not here
No bridge implementation; no eval labelling policy (but see the labelling
invariant above — it binds callers).

## Dependencies (allowed)
stdlib + `.base` + `.registry` + `..agent_loop` + `..llm` types + the dsh SDK
(imported lazily).

## Tests
`test_provider_deepseek.py`.

## Refactor notes
At ~502 LOC this is the largest transport by far, because it owns composition
generation that the CLI-based transports get from the vendor. The composition
builder (`_composition`, `_env`) is the natural split if it grows further.
