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
| 8 | RebaseTarget + locked playbook | ✅ | `playbooks/repo-rebase.yaml` (locked, L0, v2 params) — now a **monitored** delegation: live per-phase/per-module progress from the parent's state.json into RunTrace + `/status`, typed failure classification (stale-state guard included), escalation with FINAL_SUMMARY/module-log artifacts, `/resume` → parent `--resume` (`rebase/monitor.py`). Plus **`repo-rebase-native`** (candidate): the 5-phase pipeline decomposed into copilot steps that import the parent's own functions — prelude (env/log-dirs/stores via `agent.orchestrator`), phase wrappers, per-module `node_rebase_module` fan-out with wave-1 gate and parent-resume-granularity skip, patch gate, push-guarded phase 4, comparison artifact (`engine/rebase_native_steps.py`). Invisible to the planner until promoted; run via `--playbook repo-rebase-native` |
| 9 | PR rebase | ✅ here | `engine/pr_steps.py` + `playbooks/pr-rebase.yaml` (active, L1): fork-aware checkout → rebase (conflicts: agent-resolve or abort+escalate, workspace always restored) → analyze modules → per-module verify → patch gate → push with-lease to the PR head only |
| 10 | PR debug | ✅ here | `playbooks/pr-debug.yaml` (active, L1): failing checks → signature grouping (root-cause preferred over symptom; hard cap escalates) → per-group debug agent commits fixes → gate → **additive** push; `report_only` = read-only triage |
| 11 | PR review | ✅ here | `playbooks/pr-review.yaml` (active): fetch → review → gated post (`post` flag AND `ALLOW_POST=1`, else dry-run); live-verified on PR #4830 |
| 12 | Issue answering & filtering | ✅ here | `issue-answer.yaml` (gated post) + `issue-triage.yaml` (no number → recent open issues); live-verified triage of 20 real issues |
| 13 | Plugin zero | ✅ here | `plugins/vllm_omni/plugin.yaml` (modules, waves, push: allowed=false, protected main); consumed by `pr.analyze_diff` module mapping |
| 14 | Plugin registry + Phase-0 bootstrap | ✅ | `plugins/base.py`: resolve by name/path; deterministic fingerprint → draft plugin + BOOTSTRAP_REPORT.md, stops for human review; high-risk sections human-only |
| 15 | Conversational CLI | ✅ phases A+B | `cli.py` + `intent.py`: REPL, one-shot `-p`, `--plan-only`, `--resume`; compound commands → ordered queue with target carry-over ("rebase pr 12, then review it"); inline plan review; TaskSpec confirm; /status /logs /playbooks /resume |

## Repo-rebase promotion path (native candidate -> default)

1. Nightly keeps resolving the locked `repo-rebase` (candidates are invisible
   to `PlaybookStore.find()` — pinned by test).
2. Validate native off-nights: `omni-copilot --playbook repo-rebase-native --yes
   --task-param local_ci_only=true` first, then full runs;
   `rebase.compare_with_locked` writes COMPARISON.md (verdict equal/better/worse)
   against a locked run's `rebase_status.json`.
3. After ~3 consecutive equal/better full runs, a human flips native ->
   `status: active` (nightly still prefers locked). Final cutover is one
   reviewed commit: native -> `locked`, old -> `retired`. Rollback = revert.
   The monitored `rebase.run_external` step stays registered as the fallback.

Caveats (documented, by design): the native prelude exports the parent's
settings into this process's env (delta traced as `env_exported`) — don't run
other tasks in the same session after a native rebase; never run copilot resume
and `omni-rebase-orchestrator --resume` concurrently (copilot progress.json is
authoritative inside a copilot run; parent markers are still written so the
parent's resume works after abandoning the copilot run).

## Deliberate v1 boundaries
- Playbooks are ordered step lists with `foreach` fan-out and `when:` conditions —
  no cross-step DAG edges yet; none of the six playbooks needs one.
- PR-debug log collection uses `gh pr checks` (+ injected logs in tests);
  Buildkite REST log download (settings.buildkite_api_token) is stubbed for
  follow-up — grouping/debug/push paths are complete.
- Outward writes are double-gated everywhere: explicit `post`/push intent in the
  TaskSpec AND `ALLOW_POST`/`ALLOW_PUSH` env — both default off (dry-run).
