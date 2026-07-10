# push.py — spec

`LOC ~46 · safety primitive (push authorization) · refactor-status: ok`

## Responsibility
The single push authorization choke point + its policy/decision types.

> History: this was `targets/base.py`, the vestige of a designed "Target layer"
> that never became a real abstraction (its task-definition role is carried by
> `TaskSpec` + `Playbook`). The dead target dataclasses were removed (concision
> K1) and the module renamed to what it actually is — push authorization. There
> is no Target layer.

## Public contract
`PushPolicy`, `PushDecision`, `guard_push(policy, protected_branches)`.

## Invariants (**C4**)
- A push happens only when the policy allows it AND the branch is not protected.
- Force is with-lease only; a protected branch is never pushed to (force or
  not), regardless of policy.
- The ONLY push authorization point — `ci.push` and native phase-4 defer here.

## Scope — not here
No git execution (that is the step); no repo knowledge; no dry-run decision
(that is the step reading `ALLOW_PUSH`).

## Dependencies (allowed)
stdlib only. It is a leaf safety primitive (like `scopes.py`).

## Tests
`test_push_and_steps.py`.

## Refactor notes
Security-critical and pure — keep it dependency-free and side-effect-free. Every
push path must route through `guard_push`; a new push site that reimplements the
checks is a defect. A natural sibling of `scopes.py` (both are pure permission
primitives); if a `safety/` package is ever introduced, they belong together.
