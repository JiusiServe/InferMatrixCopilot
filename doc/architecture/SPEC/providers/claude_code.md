# providers/claude_code.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~205 · harness transport (Claude subscription) · refactor-status: ok`

## Responsibility
Run a whole agent step through the `claude` CLI on subscription auth.

## Functionality
Headless `claude -p` with `--max-turns` carrying our iteration budget, builtin
tools denied by name, the scoped tool bridge wired in via a generated MCP
config, and `modelUsage`/cost parsed back out of the JSON result.

## Public contract
`ClaudeCodeTransport` (`run_session`, `complete`), `spec = PROVIDERS["claude-code"]`.

## Invariants (**C1**, **C2**, **E2**)
- **Builtin tools are denied, not merely unused** (`_BUILTIN_DENY`). This is
  the preventive control the capability flag `builtin_tools_off` advertises; if
  the deny list stops matching the CLI's tool names the control silently
  weakens, so it is spelled out in one constant.
- The bridge MCP server is the ONLY tool surface offered
  (`_BRIDGE_SERVER = "infermatrix-tools"`), so every call still passes
  `tools.dispatch`.
- `--max-turns` maps our iteration budget to the vendor's native cap — the
  budget is enforced by the harness, not merely requested in the prompt.
- Usage is reported per model (`modelUsage`), and cost is only recorded when
  the CLI actually reports it (see `base.md`: never fabricate).
- Bridge activity is read from `bridge_trace.jsonl` by line offset so a second
  process never interleaves with the parent's `run_trace.jsonl`.

## Scope — not here
No registry membership decision; no scope construction (the step owns it); no
credential handling — subscription auth lives in the CLI's own HOME state and
this codebase never sees it.

## Dependencies (allowed)
stdlib + `.base` + `..agent_loop.AgentOutcome` + `..llm` types.

## Tests
`test_provider_claude_code.py`.

## Refactor notes
The three transports (`claude_code`, `codex`, `cursor`) share shape but differ
exactly where governance differs — resist merging them into one parameterized
class: the differences ARE the security posture.
