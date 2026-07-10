# targets/base.py — spec

`LOC ~76 · edge (push authorization) · refactor-status: ok`

## Responsibility
Target-layer data types + the single push guard.

## Public contract
`PushPolicy`, `PushDecision`, `guard_push(policy, protected_branches)`; plus
`ValidationPlan`, `ModuleTask`, `ModuleSchedule`, `RebaseRunSpec` (data).

## Invariants (**C4**)
- A push happens only when the policy allows it AND the branch is not protected.
- Force is with-lease only; a protected branch is never pushed to (force or
  not), regardless of policy.
- The ONLY push authorization point — `ci.push` and native phase-4 defer here.

## Scope — not here
No git execution (that is the step); no repo knowledge; no dry-run decision
(that is the step reading `ALLOW_PUSH`).

## Dependencies (allowed)
stdlib only.

## Tests
`test_push_and_steps.py`.

## Refactor notes
Security-critical and pure — keep it dependency-free and side-effect-free.
Every push path in the codebase must route through `guard_push`; a new push
site that reimplements the checks is a defect. The extra target dataclasses
(`ModuleTask` etc.) are lightly used — if they stay unused, a later refactor may
trim them, but they document the intended target-layer vocabulary.
