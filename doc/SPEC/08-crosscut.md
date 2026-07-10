# 08 — Cross-cutting: Review, Memory, Observability, Escalation, Metrics

Modules: `review/`, `memory/`, `run_trace.py`, `notify.py`, `metrics.py`.
These are horizontal services used across layers; each has a narrow contract and
a fail-safe posture.

---

## `review/` — conditional patch review

Three files pipeline: `diff_summary.py` → `triggers.py` → `reviewer.py`.

- **`diff_summary.py`** — **Responsibility**: the cheap, always-on first stage.
  `build_diff_summary(repo, base_ref, primary_files, trace) -> DiffSummary`
  (changed files, insertions/deletions, out-of-scope files, full-file writes,
  tests run, push requested). Deterministic; no LLM.
- **`triggers.py`** — **Responsibility**: decide when the LLM review fires.
  `evaluate_triggers(summary, settings, *, touched_modules, pre_push,
  knowledge_edit, high_risk_modules?) -> fired[]`. Seven rules:
  `out_of_scope_edits, high_risk_modules, large_diff, tests_unavailable,
  full_file_fallback, before_push, knowledge_edit`. **Invariant**: high-risk
  modules come from the caller (plugin), settings only as fallback (**A5**).
- **`reviewer.py`** — **Responsibility**: the read-only verdict.
  `run_patch_review(...)`, `run_plan_review(...)`. **Invariant (C6)**: returns
  `unavailable` without a reviewer LLM; unparseable output degrades to `revise`;
  anything but `lgtm` is not-passing. Fail-closed.
- **Scope** — review only; the review *step* (`review.patch_gate`,
  `agent.review_diff`) lives in `engine/steps/review.py` and calls these.
- **Tests** — `test_review.py`, `test_review_step.py`.

## `memory/` — debug memory & skills

- **`debug_memory.py`** — **Responsibility**: FTS5 store of failure→fix
  experience. **Invariant (D1/D3)**: a write must include repo/module/run_id/
  symptom/root_cause/fix_summary/files/verification/status; retrieval is
  top-k-by-relevance, summary-first. Facts recorded freely.
- **`skills.py`** — **Responsibility**: procedural knowledge, gated harder than
  debug memory. `SkillStore(find/propose/promote/candidates)`, `Skill` (with a
  `trigger` for recall). **Invariant (D1)**: agents may only `propose`
  (candidates file); `promote` to an active `SKILL.md` is a curator/human act.
- **Scope** — knowledge storage/retrieval. Per-repo namespacing is applied by the
  agent runtime (`_ScopedKnowledge`), not here.
- **Tests** — `test_memory.py`.

## `run_trace.py` — the audit spine

- **Responsibility** — append-only JSONL event log.
- **Public contract** — `RunTrace(path)` with `record(event, **fields)`,
  `events(name)`.
- **Invariant (E1)** — every governance claim in the codebase maps to a trace
  event: `agent_dispatch`/`agent_output`, `tool_call`/`tool_refused`/
  `out_of_scope_edit`/`full_file_write`, `patch_review*`, `push_requested`,
  `capability_gap`, `env_exported`, `posted_artifact`, `profile_*`. Facts are
  cheap and recorded freely (**D1**); this is the immutable layer under the
  curated profile.
- **Scope** — recording only. No policy, no filtering of what may be recorded.

## `notify.py` — escalation channel

- **Responsibility** — the "notify, never guess" exit.
- **Public contract** — `Notifier(settings, run_dir, trace, run_id)` with
  `escalate(reason, phase, severity, state_summary, artifacts)`; `BLOCKED_EXIT`
  (3).
- **Invariant** — a blocked run writes `ESCALATION.md`, notifies (Resend/SMTP if
  configured), and exits 3. Escalation is a first-class outcome, not an error
  path to swallow.
- **Scope** — notification only. Deciding *to* escalate is the executor's
  (typed-failure routing).
- **Tests** — covered via `test_engine.py` (routing) + escalation assertions.

## `metrics.py` — per-run CATQ

- **Responsibility** — compute and persist `metrics.json` per run.
- **Public contract** — `collect_run_metrics(run_dir, settings, status) -> dict`;
  `CATQ = Q·S/C` (quality · safety · 1/cost) per the METRICS_RESEARCH framework.
- **Invariant (E3)** — metrics are facts about a run and MUST NEVER break it;
  every failure is caught and traced. Q uses known components only
  (renormalized, `partial` flagged); safe-abstain scores on escalated runs;
  incidents derive from explicit events + existing out_of_scope/tool_refused/
  patch_review-revise.
- **Scope** — measurement only. No influence on control flow.
- **Tests** — `test_metrics.py`.

## `eval/` (offline machinery, not shipped in a run)

- **`eval/invariance.py`** — `replicate_mean`, `invariance_index` (min/mean,
  ≥2 repos), `score_invariance`, `ablation_verdict` (promote only if quality
  non-negative AND cost ratio ≤ 1.5). Pure functions; the paid cross-repo
  campaign that feeds them is `[planned]`. **Invariant**: rank on replicate
  means only (single rolls are ±0.1 noise); a missing arm reads as
  not-measured, never zero.
- **Tests** — `test_p3_machinery.py`.
