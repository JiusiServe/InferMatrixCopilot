# mcp_policy.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~141 · safety primitive (MCP structural gate) · refactor-status: ok`

## Responsibility
Re-derive a *safe* `TaskSpec` from raw MCP input, refusing anything the MCP
surface may not do — the structural guarantee that a host cannot widen the
server's permissions.

## Public contract
`enforce_mcp_policy(raw) -> TaskSpec` (raises on refusal).

## Invariants (**C2**, **C3**, **A2**)
- **It runs TWICE, and that is the design.** Once at the **boundary** (the
  server, when a tool is called) and once in the **child** (authoritative,
  right after it reads `request.json`). The child re-check exists because the
  guarantee must not depend on `request.json` being untampered: a same-user
  host process could rewrite it between reservation and execution.
- `kind` must be in `READ_ONLY_KINDS`; `post` is forced to `False`; `repo` must
  be in the allowlist; `pr`/`issue` must be positive; unknown params are
  stripped rather than passed through.
- **The allowed set is imported, never restated.** It references
  `task_spec.READ_ONLY_KINDS` directly so the policy can never drift from the
  task model — adding a write-capable kind cannot silently widen MCP.
- The MCP hosts are non-interactive: there is no `[y/N]`, so nothing here may
  fall back to "ask the user".

## Scope — not here
No run execution; no model calls; no knowledge access.

## Dependencies (allowed)
`..task_spec` + stdlib. A leaf safety primitive.

## Tests
`test_mcp.py` (tamper defense, read-only tool set).

## Refactor notes
Like `push.guard_push` and `scopes`, this is a pure permission primitive — keep
it dependency-free. Any new MCP-reachable capability must be expressed as a
change to `READ_ONLY_KINDS`, not as a special case here.
