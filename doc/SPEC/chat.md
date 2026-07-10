# chat.py — spec

`LOC ~373 · interface (conversational REPL) · refactor-status: split-candidate`

## Responsibility
The Claude-Code-style conversational REPL (default when an LLM is configured):
a persistent chat that answers questions and executes work through tools.

## Functionality
`SYSTEM_PROMPT` (repo-neutral, interpolates `default_repo`); `TOOL_DEFS`
(run_task/run_playbook/get_status/get_logs/read_run_report/list_playbooks/
repo_read/repo_grep/resume_run); `ChatSession` (history trim that never splits
tool pairs, streaming, tool round-trips, session transcript); read jail.

## Public contract
`chat_repl(copilot, assume_yes, handle_builtin)`; `ChatSession.turn`.

## Invariants
- Frontend, not a second execution path: funnels into `run_task`/`run_playbook`
  with the **same** gates; cannot widen permissions.
- `repo_read`/`repo_grep` jailed to configured repo roots + run root; `.env*`
  refused.
- Fetched GitHub content stays data (handled inside steps) (**C7**).

## Scope — not here
No planning/execution logic of its own; no repo-knowledge literals (prompt is
neutralized via `default_repo`).

## Dependencies (allowed)
`cli.Copilot` (TYPE_CHECKING only), `run_trace`, `task_spec`, `ui`.

## Extension points
New chat tool → a `TOOL_DEFS` entry + a `_dispatch_tool` branch, jailed and
gate-respecting.

## Tests
`test_chat.py`.

## Refactor notes
Mixes three concerns: tool schema/registry (`TOOL_DEFS`), the read jail, and the
turn loop. **Suggested split**: `chat_tools.py` (defs + `_dispatch_tool` +
jail) and `chat.py` (session/turn loop). The read-jail (`_allowed_roots`/
`_check_read`) is generically useful — consider hoisting to a small shared
helper if any other surface needs jailed reads.
