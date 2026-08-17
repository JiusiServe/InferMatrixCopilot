# mcp_server.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~392 · Strict background machinery (start/poll) · refactor-status: ok`

## Responsibility
Run Strict workflows for an MCP host: reserve, launch, track, and serve
results — without ever blocking a synchronous tool call.

## Functionality
Reviews take 5–12 minutes, which would blow any synchronous MCP call timeout,
so the surface is **start/poll tool pairs**: `start_review` /
`start_issue_answer` / `start_issue_triage` reserve and return a `run_id`
immediately; `get_result` (paginated via `next_offset`, capped by
`mcp_report_max_bytes`) and `get_status` (`run_status` + `progress`) poll it.

## Public contract
`CopilotMCP`, `build_mcp()`, the start/poll tools.

## Invariants (**C2**, **C3**, **E1**)
- **Safety is structural, not host-trusted.** `enforce_mcp_policy` runs here
  AND (authoritatively) in the child, so only `READ_ONLY_KINDS` ever run,
  `post` is always `False`, and only allow-listed repos are reachable —
  regardless of what a tampered `request.json` claims.
- **Every run is an isolated subprocess**
  (`python -m infermatrix_copilot --execute-reserved <id>`). Two reasons, both
  load-bearing: the copilot's stdout must stay out of this process's JSON-RPC
  stdio channel (child stdout → `<run_dir>/console.log`), and the
  process-global tracer / `last_run_dir` become per-run by construction.
- **Runs are serialized through one worker thread.**
- Polling correctness across restarts and multiple concurrent servers comes
  from `run_status.py`'s durable record + ownership-aware reconciliation, not
  from in-memory state.
- **The `mcp` SDK import is optional**, gated behind the `[mcp]` extra, and
  must never be imported by the core package — a plain CLI install stays
  dependency-free.
- `build_mcp()` exposes the V1 tool surface (the autonomous-workflow executor);
  it is **not registered by default**.

## Scope — not here
No Direct-mode logic (`thin_mcp_server.py`); no policy definition
(`mcp_policy.py`); no status file format (`run_status.py`).

## Dependencies (allowed)
stdlib + `mcp` (optional extra) + `.mcp_policy` + `.run_status` + `.cli`.

## Tests
`test_mcp.py` (tamper defense, single-writer reconciliation, pagination,
read-only tool set).

## Refactor notes
The reservation shape (create the run dir, then plan) is MCP-specific; the CLI
main path still gates BEFORE creating a run directory, so an abandoned plan
leaves no directory. Do not unify the two without preserving that difference.
