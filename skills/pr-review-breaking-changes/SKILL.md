---
name: pr-review-breaking-changes
description: PR review — when a default or protocol changes, sweep IN-REPO consumers (examples, docs, clients, tests) that still assume the old behavior; undocumented ordering assumptions deserve a comment
trigger: pr_review of changes to defaults, API/protocol behavior, or bridge/ordering logic
modules: [pr_review]
status: active
created_at: 2026-07-03
run_count: 0
---

## Diagnose
The diff changes a default (e.g. stream=True switching output format) or an
implicit contract (e.g. "first element is the parent request").

## Fix (what to look for)
- grep the repo for every in-repo consumer of the old behavior: examples/,
  docs/, recipes/, demo clients, tests — they break silently and humans flag
  exactly this class first (eval GT: #4679).
- An implicit ordering/identity assumption without a comment or assert is a
  finding: ask for a documenting comment (eval GT: #4849).
- Loosened test thresholds or removed skips need a stated justification.

## Verification
Each such comment cites the specific consumer file/line found by grep.

## Anti-patterns
- Approving because "the core logic is correct" while consumers still assume
  the old default.
