# app/core.py —— 规范

<!-- verified-against: 2026-09-26 -->

`Copilot` is the headless workflow application. It resolves a TaskSpec,
delegates reviewer verdict policy to `review.plan_gate`, confirms when needed,
executes or resumes a playbook, and reserves/executes durable runs. The CLI
imports it through `cli.copilot` for
compatibility; the application never imports CLI or MCP transports.

`Copilot` keeps reservation and run-path methods as compatibility delegates
to `app.reservation.RunReservation`. It owns workflow resolution and child
execution; it does not own idempotency indexing or run ID validation.

The pre-execution gate runs before a normal CLI run directory is created.
The child rechecks the read-only policy and checkout binding. Existing
checkpoint keys, run IDs, and blocked exit codes remain stable.

`GateOutcome`, `_mode_review_context`, and `Copilot` retain their import path
through the compatibility module. The application passes its reviewer to the
plan gate, preserving the no-human fail-closed rule. Only orchestration belongs
here; command argument parsing and stdio protocol registration remain
transport concerns.
