# engine/executor.py — spec

<!-- verified-against: 2026-08-17 -->

`LOC ~267 · engine substrate (the loop) · refactor-status: ok`

## Responsibility
Run a playbook's steps with task-agnostic guarantees: checkpoint/resume,
foreach fan-out, `when:` conditions, bounded retries, typed failure routing,
escalation.

## Functionality
`run` iterates steps; skips completed (restoring their `state_updates`); fans
out `foreach`; evaluates `when:`; retries RETRYABLE; routes BLOCKED/ESCALATE/
FORBIDDEN to the notifier; persists progress + indexes outputs.

## Public contract
`Executor(registry, settings, run_dir, trace, llm?, notifier?)`;
`run(playbook, state) -> RunOutcome(status, step_results, blocked_reason)`.
Helpers `_eval_when`, `_merge`.

## Invariants
- **B2**: resume restores `outputs.state_updates` before skipping; on success,
  `state.update(state_updates)` and index outputs by step id.
- `_merge` lifts each foreach item's `state_updates` (last-writer-wins).
- **B3**: `when:` reads TaskSpec then state; unknown key → blocked, not silent.
- **B1**: typed routing; unhandled exception → BLOCKED (never swallowed).
- Retries only on RETRYABLE, bounded by `max_step_retries`.
- **Run-scoped task params reach every step**: `state["task_spec"]["params"]`
  is merged under each step's own params, so `--task-param limit=5` is not
  silently dropped. **The playbook's own params win the merge** — several are
  safety-bearing (`force_push`, `pre_push`), so an authored invariant must not
  be overridable from the command line.
- A step span records the playbook step id and the foreach item key: one spec
  may run twice in a playbook and fan out again, so `step` alone cannot
  identify the work.

## Scope — not here
No step logic, no repo knowledge, no planning, no LLM prompts. Execution
guarantees only.

## Dependencies (allowed)
`engine/{step,registry}`; typing-only: config/llm/notifier/playbook/run_trace.

## Extension points
A new cross-step guarantee (e.g. per-step timeout) goes here; a new step
behavior does NOT.

## Tests
`test_engine.py`, `test_v2_p0.py` (resume/foreach/when integrity).

## Refactor notes
Well-scoped at ~200 lines. The `state_updates` publish/restore/merge logic is
subtle and load-bearing (it was the top v2 bug) — do not "simplify" it without
re-running the resume-integrity tests. If DAG edges are ever added (currently
ordered lists only), keep them here behind the same `RunOutcome` contract.
