# providers/cursor.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~207 · harness transport (Cursor subscription) · refactor-status: ok`

## Responsibility
Run a whole agent step through `cursor-agent` on subscription auth — the
backend with the weakest available preventive control, and therefore the one
that carries the detective fallback.

## Functionality
Headless `cursor-agent --print --force --output-format stream-json`, prompt on
STDIN, line-wise event parsing, bridge MCP config written per session, and a
mandatory post-run audit.

## Public contract
`CursorTransport` (`auth_gap`, `run_session`, `complete`),
`spec = PROVIDERS["cursor"]`.

## Invariants (**C1**, **C2**, **E2**)
- **The prompt goes on STDIN, never argv.** Linux caps a single argv entry at
  128KiB and evidence packs exceed it; passing it as an argument truncates the
  review silently.
- **Built-in tools cannot be fully disabled here**, so governance is two-layer
  and both layers are disclosed: scoped tools are OFFERED via the bridge
  (preventive where used) AND every session is post-audited
  (`providers/audit.py`), with the verdict traced and rendered in RUN_REPORT.
  The control class is stated — never a silent gap.
- The subprocess env is the `base.sanitized_env()` allowlist: the vendor CLI
  keeps its own subscription auth but must not inherit our model endpoints or
  repo credentials.

## Scope — not here
No audit rules (those live in `providers/audit.py`); no eval-specific policy —
the eval arm's extra "no PR-discussion access" rule is a ground-truth-leakage
concern and deliberately does not live in the product path.

## Dependencies (allowed)
stdlib + `.base` + `.registry` + `..agent_loop.AgentOutcome` + `..llm` types.

## Tests
`test_provider_cursor.py`.

## Refactor notes
The invocation shape was proven by the Composer eval arm
(`eval/dataset/run_cursor_arm.py`); if that script and this transport drift,
the eval arm stops measuring the product.
