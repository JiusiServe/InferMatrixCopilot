# ui.py — spec

`LOC ~164 · presentation · refactor-status: ok`

## Responsibility
Terminal rendering: streaming, spinners, markdown, color; degrade to plain text
on non-TTY/pipes.

## Functionality
`make_ui(out?)` returns a rich UI or a `PlainUI`; stream start/delta, styled
step/tool output, markdown rendering, input-history.

## Public contract
`make_ui`, `style(...)`, the UI object's `stream_*`/print methods.

## Invariants
- Presentation only — carries no control flow or run state.
- Deterministic plain-text fallback so scripted output stays stable.

## Scope — not here
No decisions about *what* to do — only *how it looks*. No task/planning/exec
logic; no repo knowledge.

## Dependencies (allowed)
`rich`; stdlib.

## Extension points
New rendered element → a method on the UI; keep the `PlainUI` fallback in sync.

## Tests
`test_ui.py`.

## Refactor notes
Clean separation. The only smell: `cli.py`/`chat.py` format some strings inline
before handing to `ui`; a refactor could move more of that formatting here so
callers pass structured data, not pre-formatted strings.
