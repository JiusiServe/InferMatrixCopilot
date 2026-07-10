# cli.py — spec

`LOC ~395 · interface + orchestration façade · refactor-status: split-candidate`

## Responsibility
The flag CLI and the `Copilot` façade: resolve → gate → execute; own the run
directory, RunTrace, notifier, and metrics wiring.

## Functionality
Arg parsing (`-p`, `--yes`, `--plan-only`, `--resume`, `--playbook`,
`--report-only`, `--task-param`, `--no-chat`); `Copilot.resolve/run_task/
run_playbook/run_queue/resume_last`; built-in REPL commands; plan-review gate +
confirm gate; single `_execute` entry.

## Public contract
`main(argv)`; `Copilot` (`resolve`, `run_task`, `run_playbook`, `run_queue`,
`resume_last`, `status`, `logs`, `playbooks`, `_execute`, `_plugin_for`,
`_resolve_repo_path`).

## Invariants
- `resolve` feeds capabilities (plugin + REPO_PATHS) to the planner.
- Plan-review gate before confirm; confirm fires for
  `confirm_required or requires_review` unless `--yes`.
- `_execute` is the single execution path (task / explicit-playbook / resume).
- Repo knowledge (protected branches, high-risk modules) comes from the plugin
  into run state (**A5**); blocked → exit 3 (`BLOCKED_EXIT`).
- `--playbook` is the only way to run a candidate.

## Scope — not here
No step logic, no repo-knowledge literals, no LLM prompts. Orchestration wiring
only.

## Dependencies (allowed)
`engine/*`, `playbooks/*`, `intent`, `task_spec`, `plugins/base`,
`push`, `review/reviewer`, `notify`, `run_trace`, `config`, `ui`,
`chat`. MUST NOT be imported by any lower layer (**§ARCH.4.2**).

## Extension points
New REPL command → `_handle_line`; new run wiring → `_execute`.

## Tests
`test_cli.py`, `test_phase_b.py`.

## Refactor notes
Two responsibilities are entangled: (1) `argparse`/REPL front-end and
(2) the `Copilot` façade (resolve/execute/metrics). **Suggested split**:
`cli.py` (arg parsing + `_handle_line` + `main`) and `copilot.py` (the
`Copilot` class). Keep `_execute` as the single execution seam either way.
## Concision — **K6** (dedupe gate+confirm)
`run_task` and `run_playbook` repeat the plan-review + `[y/N]` confirm sequence.
Extract `_gate_and_confirm(resolution, spec, assume_yes) -> bool` (~15 LOC).
Preserve: plan-review before confirm; confirm fires for `confirm_required or
requires_review`. (This is independent of the optional cli→copilot cohesion
split above.)
