# notify.py — spec

`LOC ~112 · cross-cutting (escalation) · refactor-status: ok`

## Responsibility
The "notify, never guess" exit channel.

## Functionality
`Notifier.escalate` writes `ESCALATION.md`, emails (Resend or SMTP if
configured), traces the escalation; `BLOCKED_EXIT` = 3.

## Public contract
`Notifier(settings, run_dir, trace, run_id)` with `escalate(reason, phase,
severity, state_summary, artifacts)`; `BLOCKED_EXIT`.

## Invariants
- A blocked run writes `ESCALATION.md`, notifies, and the caller exits 3.
- Escalation is a first-class outcome — never swallowed as an error path.
- Email failures are best-effort and must not mask the escalation itself.

## Scope — not here
Deciding *to* escalate is the executor's (typed-failure routing) — this file
only performs the notification.

## Dependencies (allowed)
`config`, `run_trace`; stdlib `urllib`/`smtplib`.

## Extension points
New channel (IM/webhook) → a method here, gated on its own config field;
keep `escalate` the single entry.

## Tests
Via `test_engine.py` routing + escalation assertions.

## Refactor notes
Clean. If channels multiply, introduce a small `Channel` strategy list rather
than more branches inside `escalate`.
