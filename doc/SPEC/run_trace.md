# run_trace.py — spec

`LOC ~40 · cross-cutting (audit spine) · refactor-status: ok`

## Responsibility
Append-only JSONL event log — the immutable audit layer.

## Functionality
`record(event, **fields)` appends one JSON line; `events(name)` filters by type.

## Public contract
`RunTrace(path)` with `record`, `events`.

## Invariants
- **E1**: every governance claim maps to a trace event (`agent_dispatch`/
  `agent_output`, `tool_call`/`tool_refused`/`out_of_scope_edit`/
  `full_file_write`, `patch_review*`, `push_requested`, `capability_gap`,
  `env_exported`, `posted_artifact`, `profile_*`).
- Facts are recorded freely (**D1**); this is the immutable layer under the
  curated profile.

## Scope — not here
Recording only. No policy, no filtering of what may be recorded, no reads that
drive control flow (except `events()` for diff-summary/metrics assembly).

## Dependencies (allowed)
stdlib only.

## Extension points
New event → just `record("<name>", ...)` at the site; document notable names in
`_CONSTRAINTS.md` §E1 if it backs a guarantee.

## Tests
Exercised across the suite via `trace.events(...)` assertions.

## Refactor notes
Deliberately trivial and dependency-free — keep it that way. It underpins every
governance claim, so it must never gain logic that could fail and lose an event.
