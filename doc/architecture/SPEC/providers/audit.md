# providers/audit.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~109 · detective control (post-run session audit) · refactor-status: ok`

## Responsibility
Audit a completed harness session for containment violations, for backends
where no preventive control is available.

## Functionality
Given the session's tool events, checks that file reads stayed inside the
containment roots (PR-time worktree + run dir) and that a read-only scope saw
no write/edit calls. Returns findings; never mutates anything.

## Public contract
`SessionAudit` (`ok`, `tool_calls`), `contained_in(path, roots)`,
`audit_events(events, *, roots, ...)`.

## Invariants (**C1**, **C2**, **E2**)
- **Detective, not preventive** — the *disclosed fallback* of the tool
  governance decision. It runs for cursor-agent, whose built-in tools cannot be
  disabled. It does not stop anything; it reports.
- **Findings are surfaced, never silently dropped.** Violations go to the
  caller to trace and render in RUN_REPORT. A silent audit is worse than none,
  because it implies a control that is not in force.
- **Product policy only.** The eval arm layers an extra "no PR-discussion
  access" rule on top; that is a ground-truth-leakage concern, not a product
  one, and deliberately does NOT live here.
- **One documented exemption:** cursor-agent spools MCP tool *results* into its
  per-project state dir and reads them back with its native read tool
  (`_CLI_TOOL_SPOOL`). That read-back is how bridge output is consumed, not
  exfiltration — without the exemption every bridge-using session was flagged
  (live-smoke finding).

## Scope — not here
No enforcement; no vendor invocation; no eval-specific rules.

## Dependencies (allowed)
stdlib only. A leaf analysis module.

## Tests
Covered via `test_provider_cursor.py`.

## Refactor notes
Productized from `eval/dataset/run_cursor_arm.py`, which caught a live
out-of-bounds read (`~/.claude/skills/...`) through exactly this check. Keep it
pure so the eval arm and the product path cannot diverge in judgement.
