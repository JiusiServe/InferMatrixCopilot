# Implementation status vs the design's 15 tasks

Task numbers from `copilot_design` §四 (milestones from `docs/copilot/implementation/`).
"Here" = implemented in this repo, offline-tested (64 tests).

| # | Design task | Status | Where / notes |
|---|---|---|---|
| 0 | Freeze + regression harness | ✅ here (adapted) | greenfield repo, so the harness is the test suite; the nightly rebase is untouched (delegated, not forked) |
| 1 | ToolScope / PathScope | ✅ here | `scopes.py` + `tools.dispatch` choke point; pre/post-plan scopes; out-of-scope recorded |
| 2 | DispatchContext | ✅ here (as StepContext/TaskSpec) | structured inputs `engine/step.py::StepContext`, `task_spec.py`; parent-agent prompt-builder split still pending upstream |
| 3 | Memory governance | ✅ here | `run_trace.py`; `memory/debug_memory.py` write contract + summary retrieval; `memory/skills.py` propose→promote gate |
| 4 | Engine substrate + Step library | ✅ here | `engine/` — 20 registered steps; foreach fan-out; `when:` TaskSpec conditions; per-step checkpoint/resume; typed failures |
| 5 | Playbook registry + reuse>adapt>generate | ✅ here | `playbooks/store.py`, `engine/planner.py`; locked refuses adapt; generate read-only-only; candidates never auto-recalled; all six task kinds recall a vetted playbook |
| 6 | Escalation channel | ✅ here | `notify.py`: ESCALATION.md + Resend/SMTP email + exit 3; wired into executor failure routing |
| 7 | Conditional Patch Review | ✅ here | `review/`: always-on diff summary, 7 trigger rules, read-only reviewer, fail-closed; **plan review** (`run_plan_review`) gates adapted/generated plans inline in the CLI |
| 8 | RebaseTarget + locked playbook | ✅ | `playbooks/repo-rebase.yaml` (locked, L0) delegating to the existing orchestrator; `targets/base.py` types + `guard_push`. Native ModuleSchedule decomposition stays in the parent repo per milestone M2 |
| 9 | PR rebase | ✅ here | `engine/pr_steps.py` + `playbooks/pr-rebase.yaml` (active, L1): fork-aware checkout → rebase (conflicts: agent-resolve or abort+escalate, workspace always restored) → analyze modules → per-module verify → patch gate → push with-lease to the PR head only |
| 10 | PR debug | ✅ here | `playbooks/pr-debug.yaml` (active, L1): failing checks → signature grouping (root-cause preferred over symptom; hard cap escalates) → per-group debug agent commits fixes → gate → **additive** push; `report_only` = read-only triage |
| 11 | PR review | ✅ here | `playbooks/pr-review.yaml` (active): fetch → review → gated post (`post` flag AND `ALLOW_POST=1`, else dry-run); live-verified on PR #4830 |
| 12 | Issue answering & filtering | ✅ here | `issue-answer.yaml` (gated post) + `issue-triage.yaml` (no number → recent open issues); live-verified triage of 20 real issues |
| 13 | Plugin zero | ✅ here | `plugins/vllm_omni/plugin.yaml` (modules, waves, push: allowed=false, protected main); consumed by `pr.analyze_diff` module mapping |
| 14 | Plugin registry + Phase-0 bootstrap | ✅ | `plugins/base.py`: resolve by name/path; deterministic fingerprint → draft plugin + BOOTSTRAP_REPORT.md, stops for human review; high-risk sections human-only |
| 15 | Conversational CLI | ✅ phases A+B | `cli.py` + `intent.py`: REPL, one-shot `-p`, `--plan-only`, `--resume`; compound commands → ordered queue with target carry-over ("rebase pr 12, then review it"); inline plan review; TaskSpec confirm; /status /logs /playbooks /resume |

## Deliberate v1 boundaries

- The nightly rebase remains one locked external step (`rebase.run_external`);
  decomposing it into native waves/module-agent steps is parent-repo milestone
  M2 work and must land there first (zero-regression harness lives there).
- Playbooks are ordered step lists with `foreach` fan-out and `when:` conditions —
  no cross-step DAG edges yet; none of the six playbooks needs one.
- PR-debug log collection uses `gh pr checks` (+ injected logs in tests);
  Buildkite REST log download (settings.buildkite_api_token) is stubbed for
  follow-up — grouping/debug/push paths are complete.
- Outward writes are double-gated everywhere: explicit `post`/push intent in the
  TaskSpec AND `ALLOW_POST`/`ALLOW_PUSH` env — both default off (dry-run).
