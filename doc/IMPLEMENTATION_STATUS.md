# Implementation status vs the design's 15 tasks

Task numbers from `copilot_design` §四 (milestones from `docs/copilot/implementation/`).
"Here" = implemented in this repo, offline-tested.

| # | Design task | Status | Where / notes |
|---|---|---|---|
| 0 | Freeze + regression harness | ✅ here (adapted) | this repo is greenfield, so the harness is the 49-test suite; the nightly rebase is untouched (delegated, not forked) |
| 1 | ToolScope / PathScope | ✅ here | `scopes.py` + `tools.dispatch` choke point; pre/post-plan scopes; out-of-scope recorded |
| 2 | DispatchContext | ✅ here (as StepContext/TaskSpec) | structured inputs `engine/step.py::StepContext`, `task_spec.py`; parent-agent prompt-builder split still pending upstream |
| 3 | Memory governance | ✅ here | `run_trace.py`; `memory/debug_memory.py` write contract + summary retrieval; `memory/skills.py` propose→promote gate |
| 4 | Engine substrate + Step library | ✅ here (v1) | `engine/` — 11 builtin steps; foreach fan-out; per-step checkpoint/resume; typed failures |
| 5 | Playbook registry + reuse>adapt>generate | ✅ here | `playbooks/store.py`, `engine/planner.py`; locked refuses adapt; generate read-only-only; candidates never auto-recalled |
| 6 | Escalation channel | ✅ here | `notify.py`: ESCALATION.md + Resend/SMTP email + exit 3; wired into executor failure routing |
| 7 | Conditional Patch Review | ✅ here | `review/`: always-on diff summary, 7 trigger rules, read-only reviewer, fail-closed |
| 8 | RebaseTarget + locked playbook | ✅ v1 | `playbooks/repo-rebase.yaml` (locked, L0) delegating to the existing orchestrator; `targets/base.py` types + `guard_push`. Native ModuleSchedule decomposition: pending |
| 9 | PR rebase | 🔶 partial | push guard (force-with-lease, protected-branch refusal) + TaskSpec/tier ready; checkout/replay/verify steps pending |
| 10 | PR debug | 🔶 partial | TaskSpec + adapt path ready; Buildkite failure collection/grouping steps pending (reuse parent agent's monitor) |
| 11 | PR review | ✅ v1 (dry-run) | generated L2 plan: `pr.fetch_diff` → `agent.review_diff` → report; posting comments deliberately not implemented yet |
| 12 | Issue answering & filtering | ✅ v1 (draft-only) | `issue.fetch` → `agent.draft_issue_answer` / `agent.triage_issues`; never auto-posts |
| 13 | Plugin zero | ✅ here | `plugins/vllm_omni/plugin.yaml` (modules, waves, push: allowed=false, protected main) |
| 14 | Plugin registry + Phase-0 bootstrap | ✅ v1 | `plugins/base.py`: resolve by name/path; deterministic fingerprint → draft plugin + BOOTSTRAP_REPORT.md, stops for human review; high-risk sections human-only |
| 15 | Conversational CLI | ✅ phase A | `cli.py` + `intent.py`: REPL, one-shot `-p`, `--plan-only`, TaskSpec confirm, /status /logs /playbooks; task queue + inline review = phase B, pending |

## Known v1 simplifications

- The executor is sequential-with-foreach-fan-out; no cross-step DAG edges yet
  (playbooks are ordered lists — sufficient for all current playbooks).
- `rebase.run_external` treats the 5-phase orchestrator as one locked script
  step; step-level decomposition of the rebase happens in the parent repo per
  milestone M2 before it can move here.
- Reviewer/intent LLM calls are single-shot (no tool use); the tool-using
  `agent_loop.py` exists and is scope-tested, ready for richer agent steps.
- `gh` CLI is the GitHub transport; steps degrade to BLOCKED (never crash)
  when it is absent.
