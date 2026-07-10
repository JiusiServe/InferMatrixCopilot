# scopes.py — spec

`LOC ~94 · engine (permissions) · refactor-status: ok`

## Responsibility
Path-level tool permissions — the permission vocabulary the dispatcher enforces.

## Functionality
`ToolScope.check` (tool allowed? write path allowed?); `PathScope.check_write`
(writable hard wall + primary owned-files); scope factories.

## Public contract
`ToolScope(name, allowed_tools, path_scope?, read_only)`; `PathScope(writable,
primary)`; `Decision`; `read_only_scope`, `pre_plan_scope`, `post_plan_scope`;
tool-set constants (READ/WRITE/EXEC).

## Invariants
- Three outcomes: allowed / refused (tool not in set, write outside `writable`,
  or read-only scope) / out-of-scope (inside `writable` but outside `primary` —
  allowed + recorded).
- `writable` is a hard wall; `primary` defines the module's owned files.

## Scope — not here
Permission decisions only — no execution, no tracing (the dispatcher traces).

## Dependencies (allowed)
stdlib only.

## Extension points
New scope shape → a factory function; keep the three-outcome `Decision` contract.

## Tests
`test_scopes_tools.py`.

## Refactor notes
Clean, dependency-free, security-critical. Keep it pure (no side effects) so it
stays trivially testable. `engine/step.py` imports it — do not add a back-import.
