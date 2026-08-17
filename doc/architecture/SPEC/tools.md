# tools.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~228 · engine (capabilities + choke point) · refactor-status: ok`

## Responsibility
Atomic capabilities + the single scope-enforcing dispatch choke point.

## Functionality
Defines builtin tools (read_file, write_file, edit_file, list_dir, grep,
run_shell); `dispatch` scope-checks, runs, and traces each call.

## Public contract
`ToolDef`; `TOOLS`; `tool_definitions_for(scope, extra?)`;
`dispatch(name, args, *, scope?, trace?, extra?) -> {ok, result|error,
out_of_scope}`.

## Invariants (**C3**)
- Every builtin call is scope-checked; refused → error return (never raise).
- Out-of-scope write executes but emits `out_of_scope_edit`; full-file `.py`
  write emits `full_file_write`.
- Errors are observations, not crashes.
- Extra (step-provided) tools bypass the builtin allowlist but are still traced.
- **`read_file` is windowed (48k chars, `offset` paging), not whole-file.** A
  full-file read blows up the conversation history, multiplies uncached tokens,
  and pushes the session past reliable cache length — a measured cost, not
  caution.
- **`grep` matches LITERALLY by default** (`regex:true` opts in), so searching
  `items[0]` needs no escaping. A regex-by-default tool silently mis-answers
  the most common query shape.
- The same `dispatch` serves harness backends through `tool_bridge.py`, so
  changing enforcement here changes it for every backend at once.

## Scope — not here
"What can be done" only — tools express capability, not engineering semantics
(that is a step, **A3**). No task/repo logic.

## Dependencies (allowed)
`run_trace`, `scopes`; stdlib.

## Extension points
New builtin tool → a `ToolDef` in `TOOLS` (declare `write_path_arg` if it
writes). Step-specific tools are passed as `extra`, not added here.

## Tests
`test_scopes_tools.py`.

## Refactor notes
The dispatch choke point is a hard security invariant — every path (builtin and
extra) must remain traced and scope-checked. Do not add a "fast path" that
bypasses `dispatch`. Fine at current size.
