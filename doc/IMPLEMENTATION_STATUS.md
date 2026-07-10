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
| 11 | PR review | ✅ v4 | `playbooks/pr-review.yaml`@4: deterministic `pr.gate_check` (draft/merge-state/failing CI) + evidence-grounded two-stage `agent.review_diff` (tool-loop investigation over the repo checkout, domain checklist incl. undocumented assumptions, severity/[unverified] labels, verify-and-rewrite editor) → gated post. Eval-informed (eval/ANALYSIS.md `copilot_v2`): actionability 0.81–0.91 vs 0.50, 5/8 GT issues reachable across samples vs 2/8. Claude Code engine remains eval-only |
| 12 | Issue answering & filtering | ✅ here | `issue-answer.yaml` (gated post) + `issue-triage.yaml` (no number → recent open issues); live-verified triage of 20 real issues |
| 13 | Plugin zero | ✅ here | `plugins/vllm_omni/plugin.yaml` (modules, waves, push: allowed=false, protected main); consumed by `pr.analyze_diff` module mapping |
| 14 | Plugin registry + Phase-0 bootstrap | ✅ | `plugins/base.py`: resolve by name/path; deterministic fingerprint → draft plugin + BOOTSTRAP_REPORT.md, stops for human review; high-risk sections human-only |
| 15 | Conversational CLI | ✅ phases A+B+C | `cli.py` + `intent.py`: one-shot `-p`, `--plan-only`, `--resume`; compound commands → ordered queue with target carry-over; inline plan review; TaskSpec confirm. **Phase C** (`chat.py`): Claude-Code-style interactive chat is the default REPL — persistent history (trim never splits tool pairs), streaming replies, tool round-trips (run_task/run_playbook via the same confirm gates, status/logs/reports, repo_read/repo_grep jailed to configured repos with `.env*` refused), session transcripts under `~/.omni-copilot/sessions/`; `--no-chat` keeps the deterministic REPL |

## Agent Step 修正方案 (code review of 2026-07-03) — status

Implemented per its own P0-P3 plan (`/rebase/vLLM-Omni Copilot Agent Step 修正方案.md`):
- **P0** `engine/agent_runtime.py::run_agent_step` — the single entry for every
  `kind == "agent"` step: AgentDispatchContext (task/step/repo/evidence/
  previous-steps/permissions/skills/memories/output-contract), evidence pack
  replacing 60k truncation (per-item cap + full text archived in the run dir),
  base+extension JSON output contract with one repair round, typed
  status→FailureKind mapping, agent_dispatch/agent_output RunTrace events with
  token cost; budget-exhausted runs force a final answer instead of discarding
  the investigation.
- **P1** migrated read-only steps: `agent.review_diff` (review_comments
  contract, deterministic markdown render), `agent.draft_issue_answer`,
  `agent.triage_issues`; read-only gh tools (`gh_pr_view`/`gh_issue_view`/
  `gh_ci_read`) + knowledge tools (`skill_search`/`memory_search`/
  `skill_update_candidate` — candidates only, curator-gated). Skills seeded
  under `skills/` and retrieved per task into the dispatch context.
- **P2** migrated write steps: `agent.debug_group` (root_cause/fix_summary/
  verification contract) and the conflict agent inside `pr.rebase_onto_base` —
  both on PathScoped write scopes through the dispatcher (out-of-scope edits
  recorded); playbook patch gates unchanged as the post-edit review condition.
- **P3** cleanup: `_agent_step` factory deleted; `agent.verify_module`
  re-kinded `validation` (plain-LLM advisory, no longer masquerading);
  `rebase.module_rebase` re-kinded `script` (delegation to the parent's own
  governed agent). `kind == "agent"` now means unified-runtime-governed —
  pinned by a parametrized test asserting the agent_dispatch event.
- Locked repo-rebase playbook untouched (acceptance #10).

### Ensemble agent steps (robustness follow-up, 2026-07-05)
`run_agent_step_ensemble` (agent_runtime.py): the eval showed single agent-step
runs have high variance (RQS 0.11–0.38 on identical configs) while the UNION of
runs covered 5/8 ground-truth issues — so the runtime now offers a
perspective-diverse fan-out (each sample goes deep on one lens of the step's
checklist) followed by a verify-and-merge reduction (dedupe with consensus
weighting, per-item verification against the evidence, self-contained
rewrite). Fail-open: if the reduction itself fails, the unverified union is
returned rather than losing the samples. `agent.review_diff` uses a 3-lens
ensemble (logic / behavior / contracts) by default (`REVIEW_ENSEMBLE=0` to
disable); the mechanism is step-agnostic — any agent step with a list-valued
extension output (triage rows, debug hypotheses) can adopt it by passing
lenses + merge guidance. Eval result (sample E): RQS 0.34 — best arm on both
metrics, above claudecode_skill (0.27) and the old single-shot (0.26), at
~740k tokens/review. Reducer hardening pinned by tests: deterministic base-
field merge (whole-contract re-emission truncates), status from samples (the
reducer conflates step status with the artifact's verdict), no repair round
on empty reducer output, fail-open to unverified union.

### Ensemble v2 — parallel lenses + per-item verdict reduction (2026-07-06)
Six-cycle optimization campaign (eval/ANALYSIS.md "Optimization campaign"):
- Lenses now run **concurrently** (`ENSEMBLE_PARALLEL`, default on;
  `run_agent` offloaded via `asyncio.to_thread`, RunTrace append is locked,
  evidence archiving atomic): review wall-clock 12.8 → ~6 min; lens count is
  free in time. A 4th `verification` lens (named test/benchmark + regression
  risk) joined logic/behavior/contracts.
- The reducer no longer re-emits the merged list (free-form regeneration
  silently lost findings): it returns one keep/drop/dup verdict per NUMBERED
  candidate; code assembles deterministically; **unmentioned candidates are
  kept** (fail-open per item). Repo-cited claims are judged on the coherence
  of the cited evidence — the reducer holds only the diff pack and must not
  drop what it cannot see (info-asymmetry fix). Comment budget is code-side
  (severity-ordered cap 5).
- Verdict coherence: severities above nit mean "belongs in this PR", so any
  such comment ⇒ REQUEST CHANGES (deterministic in `_render_review_md`).
  Decision correctness vs human outcomes went 0.33 → 1.00 in 14/15 PR-runs —
  the most reproducible gain of the campaign.
- `ENSEMBLE_SAMPLES_PER_LENS` (default 1): ×2 measured 2× cost, no recall
  gain. RQS3 across replicate runs: best single run 0.686 (RQS3e 0.505),
  shipped-config runs 0.58-0.59 — recall/precision judge+generation noise is
  ±0.1 RQS3 per run; see the campaign table before trusting any single roll.
- **Final measured result (2026-07-06)**: the shipped configuration scores
  **RQS3 0.663 / RQS3e 0.509** as the mean over 3 full replicates under the
  corrected v3.1 judge (runs 0.75/0.65/0.59 — decision 1.00 and precision
  0.83-0.91 in every run; archives in
  eval/raw/copilot_v2_samples/sample_{M,N,O}_iter7_run*). Two enablers:
  the METRIC_V3.md v3.1 rubric fix (the validity jury voted requested-change
  findings invalid because the requested change is absent from the diff;
  fixing it raised cross-judge κ from 0.00 to 0.63) and replicate-mean
  scoring (eval/run_replicates.sh + score_replicates.py) — several
  plausible "improvements" (tool-looped reducer, per-lens output floors,
  tighter caps/budgets) measured WORSE on replicate means and were
  reverted. Two safeguards were kept beyond the measured config:
  deterministic sweep-target enumeration and the consensus-gated fast path
  (a single-lens singleton always faces the reducer — a fabricated-evidence
  blocker once sailed through unverified).

### Run metrics — CATQ machinery (2026-07-06)
`metrics.py` implements eval/METRICS_RESEARCH.md's cross-task framework:
`CATQ = Q·S/C` per run, written to `<run-dir>/metrics.json` after every run
(cli, `metrics_enabled`, failures never break the run). Q = weighted
arithmetic mean per task kind over KNOWN components only (renormalized,
`partial` flagged; judged/GT components are merged later via
`extra_components` — never fabricated); fixed safe-abstain scores
(rebase 0.35 / answer 0.30 / debug 0.25) on escalated-blocked runs. S =
geometric per-incident decay (severe 0.5, moderate 0.8, minor 0.95), hard
zero on catastrophic; incidents derive from explicit `incident` events
(`record_incident`) plus existing out_of_scope_edit/tool_refused/
patch_review-revise. C = RQS3e-style log cost index over USD (price table +
settings overrides, CI minutes·rate) and wall-clock vs per-task reference
budgets (settings.cost_ref_usd/min). Instrumentation added: posted_artifact
events (comment URL) on real posts, pre-fix ci_check_snapshot in
pr.fetch_ci_failures (F2P/P2P before-state), reducer token usage on
agent_ensemble events, llm_usage on agent.verify_module. Offline tests in
test/test_metrics.py. Not yet built (per the doc's roadmap): the gh feedback
collector filling useful/accepted/conflict online, post-push CI snapshot,
per-hunk conflict records, dashboards.

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

## Design v2 (doc/DESIGN.md Part II) — status

**P0 — correctness (2026-07-10, done):** the §V2.1(a) fixes, pinned by
`test/test_v2_p0.py`:
- Resume state contract: every state key a later step consumes is published
  via `outputs.state_updates` (fetch/gate/review/issue/checkout/rebase/
  analyze/ci steps; PushPolicy serialized JSON-simple, `ci.push` rehydrates).
  Previously `--resume` past a completed fetch re-entered review with no
  `diff_text` (spurious BLOCKED) and resumed pr-rebase pushes saw the
  deny-all default policy (spurious FORBIDDEN).
- `_merge` lifts fan-out items' `state_updates` into the merged result.
- `when:` reads TaskSpec first, then state keys; unknown keys block loudly
  instead of silently evaluating false.
- Per-repo knowledge wired: agent runtime resolves the repo plugin's
  `skills/` + `store/debug_memory.db` ahead of the shared pool; proposals
  land in the repo namespace (`_ScopedKnowledge`).
- High-risk modules come from the plugin (`modules.<m>.risk: high` in
  plugin zero) via run state; `settings.high_risk_modules` is fallback only.
- `test_repo_neutral_core`: repo-specific literals in `src/` are capped at
  the known v1 leak list (§V2.1(b)) — it can only shrink.

P1 (profile substrate), P2 (repo-neutral execution), P3 (measured
invariance): not started — see doc/DESIGN.md §V2.4.

## Deliberate v1 boundaries
- Playbooks are ordered step lists with `foreach` fan-out and `when:` conditions —
  no cross-step DAG edges yet; none of the six playbooks needs one.
- PR-debug log collection uses `gh pr checks` (+ injected logs in tests);
  Buildkite REST log download (settings.buildkite_api_token) is stubbed for
  follow-up — grouping/debug/push paths are complete.
- Outward writes are double-gated everywhere: explicit `post`/push intent in the
  TaskSpec AND `ALLOW_POST`/`ALLOW_PUSH` env — both default off (dry-run).
