# run_status.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~247 · durable single-writer run lifecycle record · refactor-status: ok`

## Responsibility
`run_status.json` — the durable, unambiguous lifecycle record of one Strict
run, observable across processes.

## Functionality
The server launches each run as a subprocess and can only observe it through
the filesystem, so state must survive a server restart and must distinguish a
crashed run from a running one (file-presence heuristics cannot).

## Public contract
`reserve_run`, `mark_child_started`, `read_status`, state constants
(`queued`/`planning`/`running`/terminal/`interrupted`/`FAILED`).

## Invariants (**C3**, **E1**)
- **Single writer.** `reserve_run` (server, before the child exists) writes
  `queued`; once launched the **child is the sole writer** during the run,
  writing its own pid via `mark_child_started` as its first act, then
  `planning → running → terminal`. The parent only reconciles after `.wait()`
  — i.e. after the child is known dead.
- **Cross-process reconciliation happens only once the writer is confirmed
  dead**, under `flock`, preserving the owner fields.
- **Ownership-aware reconciliation** (`owner_server_id` / `owner_server_pid` /
  `child_pid`): only the *owning* server being confirmed dead may mark a
  non-terminal run `interrupted`. Under the multi-server model (Claude Code and
  Codex each launch their own server) this is what stops one server from
  stealing another's live `queued` run.
- **No run stays non-terminal forever**: reconciliation runs lazily on every
  `get_*`, after the parent's `wait()`, and on startup scan — three places.

## Scope — not here
No process launching (that is `mcp_server`); no policy; no report rendering.

## Dependencies (allowed)
stdlib only (`json`, `os`, `fcntl`/`flock`, `pathlib`).

## Tests
`test_mcp.py` (single-writer reconciliation, ownership).

## Refactor notes
Every change here must be reasoned about with two servers and a dead child in
mind; "simplify by dropping the owner fields" reintroduces cross-server run
theft.
