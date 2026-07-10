# tools.py — spec

`LOC ~162 · engine (capabilities + choke point) · refactor-status: ok`

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
