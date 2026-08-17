# tool_bridge.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~308 · scoped-tool MCP server for harness sessions · refactor-status: ok`

## Responsibility
Expose the run's scoped tools to a harness session as an stdio MCP server, so
that delegating a step to a vendor agent does not delegate away the permission
gate.

## Functionality
`python -m infermatrix_copilot.tool_bridge --spec <bridge_spec.json>` — a
server a harness launches from its MCP config. Serves the run's builtin tools,
`doc_search`/`doc_read`, the on-demand `repo_map`, and the read-only
change-archaeology set (`diff_stat`, `file_at_base`, `show_commit`,
`search_history`, `calc`).

## Public contract
`write_bridge_spec(...)`, `load_bridge_spec(path)`, `make_dispatcher(...)`,
`build_server(spec_path)`, `main(argv)`.

## Invariants (**C1**, **C2**, **E2**)
- **Every builtin call passes `tools.dispatch`** with the step's deserialized
  `ToolScope`, so refusals, relative-path resolution against the PR-time
  worktree, and result bounds behave identically to the in-process loop.
- **Reads are contained — STRONGER than in-process.** `ToolScope` path-guards
  only writes; a harness is a less-trusted caller holding an untrusted PR diff,
  so the bridge refuses read/list/grep targets outside the containment roots
  (scope root + run dir). This is the `.env`-exfiltration guard.
- **A separate trace file.** Tool events append to `bridge_trace.jsonl` beside
  the spec; a second process must never interleave with the parent's
  `run_trace.jsonl`.
- **`repo_map` failure degrades, never crashes** — a traced
  `capability_gap` (`bridge.repo_map`).
- **skill/memory retrieval is deliberately NOT bridged.** Those tools propose
  knowledge candidates; opening a cross-process write path was declined. A
  harness session may read this repo's knowledge, never add to it.

## Scope — not here
No transport invocation (each `providers/<id>.py`); no scope construction (the
step owns it); no knowledge writes, ever.

## Dependencies (allowed)
stdlib + `mcp` (the `[mcp]` extra) + `..tools` + `..scopes` + `..run_trace` +
knowledge/repo-map factories.

## Tests
`test_tool_bridge.py`.

## Refactor notes
Not every backend can reach this server: `providers/deepseek.py` runs on the
harness's native bash because its bundled runtime carries no MCP client, and
traces a `capability_gap` when handed a spec it cannot honour. Any claim that
a run was "tools bridged" must be checked against that flag, not assumed from
the backend being a harness.
