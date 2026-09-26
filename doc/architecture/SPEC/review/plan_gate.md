# review/plan_gate.py — plan-review policy

<!-- verified-against: 2026-09-26 -->

This component builds the authoritative mode-aware context for a planned
playbook and interprets the injected plan reviewer's verdict. Exact reused
plans that do not require review pass without a reviewer call. A `block`
verdict always stops; `revise` or `unavailable` stops an unattended `--yes`
run because no person remains to inspect the plan. Interactive runs surface
those verdicts and leave final confirmation to `app.core`.

The mode context uses the executor's `when` evaluation and resolved rebase
mode, so inactive write/push steps are not presented as active. It does not
execute a plan, print notices, prompt for confirmation, create a run directory,
or own a transport. It returns a `PlanGateResult` with the decision and notices;
`app.core` renders them and keeps `_mode_review_context` and
`_plan_review_gate` compatibility entry points while supplying the reviewer.

Verification: `test_planner_playbooks.py`, `test_curator.py`, and
`test_phase_b.py` cover verdicts, mode context, and the application gate.
