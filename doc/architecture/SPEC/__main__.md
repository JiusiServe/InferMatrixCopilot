# __main__.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~12 · module entry point · refactor-status: trivial`

## Responsibility
`python -m infermatrix_copilot` — the entry the MCP server uses to launch a
reserved run.

## Invariants (**C3**, **E1**)
- The server launches the child as
  `sys.executable -m infermatrix_copilot --execute-reserved <run_id>`, i.e.
  **with the current interpreter**, so the child inherits the same environment
  the server was installed into.
- The child must be a **separate process**, not a thread: its stdout goes to
  the run's `console.log` (the server's own stdout carries JSON-RPC only), and
  the process-global tracer / `last_run_dir` become per-run by construction.

## Scope — not here
No logic. It delegates to `cli.main` and must stay that thin.

## Dependencies (allowed)
`.cli`.

## Tests
Exercised by `test_mcp.py` (which launches a real subprocess).

## Refactor notes
Adding anything here would run before `cli.main`'s gates.
