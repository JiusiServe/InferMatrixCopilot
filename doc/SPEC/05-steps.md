# 05 — The Step Library (`engine/steps/`)

38 vetted steps across 8 domain modules + `_common.py`, self-registering via
`@step` / `register_step` (§01-A4). `steps/__init__.register_builtin_steps`
flushes the collected specs into a `StepRegistry`.

## Package-wide rules

- **A step = one stable engineering action** with declared `kind`, `risk`, I/O,
  success criteria, and failure semantics (**A3**). Too fine (a single tool call)
  or too coarse (a whole task) does not belong here.
- **Kinds**: `deterministic` (no LLM), `script` (delegates to governed external
  logic), `agent` (governed via `run_agent_step` — **B4**), `validation`
  (plain-LLM advisory), `report`.
- **Risk**: honest and minimal (`read` < `write_workspace`/`knowledge` < `push`).
  The planner and patch-review triggers rely on it being truthful.
- **State handoffs** via `outputs.state_updates` (**B2**). **Typed failures**
  only (**B1**).
- **No cross-step imports**; shared code → `_common.py` (**A2**). **No repo
  literals** (**A5**) — the sole exceptions are the delegation files
  `rebase_ext.py`/`rebase_native.py` (they name the parent package by design,
  capped by the leak test).

---

## `steps/_common.py`

- **Responsibility** — the registration surface + cross-module helpers.
- **Public contract** — `step(name, kind, risk, description, *, tool_scope?,
  patch_review_triggers?)` decorator; `register_step(StepSpec)`; `collected()`;
  helpers `repo_path`, `task_spec`, `gh`, `git`, `gh_read_tools`, `post_step`.
- **Invariants** — the only home for step-shared helpers; duplicate step name →
  raise at import. Helpers are thin, side-effect-honest, and repo-neutral.
- **Scope** — infrastructure + shared IO helpers. No step handlers here.

## `steps/workspace.py`

- **Steps** — `workspace.guard_clean` (deterministic/read), `analysis.diff_summary`
  (deterministic/read).
- **Invariant** — `guard_clean` refuses to start on a dirty tree (BLOCKED) — the
  precondition for any write-capable run.

## `steps/rebase_ext.py`

- **Steps** — `rebase.run_external` (script/write_workspace).
- **Responsibility** — monitored subprocess delegation to the locked 5-phase
  orchestrator (wrap-don't-rewrite).
- **Invariants** — zero-regression: does not reimplement the pipeline; streams
  parent `state.json` into RunTrace; stale-state guard prevents a previous run's
  `phase=done` masking a crash; failures classified into escalation material.
  Names the parent package (allowed repo literal).

## `steps/review.py`

- **Steps** — `review.patch_gate` (validation/read, `patch_review_triggers=
  (before_push,)`), `agent.review_diff` (agent/read, read-only scope).
- **Responsibility** — conditional patch review; the PR-review agent step + its
  repo-neutral prompt system (`_REVIEW_SYSTEM`, `_REVIEW_LENSES`,
  `_REVIEW_MERGE`, `_sweep_targets`, `_render_review_md`).
- **Invariants** — patch gate: cheap summary always, LLM review only when a
  trigger fires; fail-closed (**C6**); high-risk modules from the plugin,
  settings fallback (**A5**). Review: domain checklist extends from the profile's
  `review.md`; `_sweep_targets` extractors keyed on `repo.language` and degrade
  honestly; verdict coherence (any ≥minor comment ⇒ REQUEST CHANGES);
  deterministic severity-ordered comment cap. Re-exported by the `builtin_steps`
  shim (`_REVIEW_LENSES`, `_render_review_md`, `_sweep_targets`).
- **Tests** — `test_review_step.py`, `test_agent_ensemble.py`,
  `test_profile_steps.py::test_review_guidance_from_profile`.

## `steps/pr.py`

- **Steps** (11) — `ci.push` (script/push); `pr.fetch_diff`, `pr.gate_check`,
  `pr.checkout_branch`, `pr.analyze_diff`, `pr.fetch_ci_failures`,
  `pr.group_failures` (deterministic/read); `pr.rebase_onto_base`,
  `agent.debug_group` (agent/write_workspace); `agent.verify_module`
  (validation/read); `pr.post_review` (script/push).
- **Invariants** — `ci.push` delegates all safety to `guard_push` (**C4**).
  `pr.checkout_branch` derives the `PushPolicy` and publishes it serialized
  (**B2**) — resuming at push must see it, not the deny-all default.
  `pr.rebase_onto_base` resolves conflicts via a governed agent or aborts +
  escalates (workspace always restored). `pr.fetch_ci_failures` enriches logs
  via the profile-selected CI provider or records a `capability_gap` (**E2**);
  `pr.group_failures` groups by **normalized** signature (**§07** ci/normalize).
  `pr.post_review` is double-gated (**C5**). `extract_signature` re-exported by
  the `pr_steps` shim.
- **Tests** — `test_pr_steps.py`, `test_push_and_steps.py`, `test_ci_and_repo_map.py`.

## `steps/issue.py`

- **Steps** (4) — `issue.fetch` (deterministic/read); `agent.draft_issue_answer`,
  `agent.triage_issues` (agent/read, read-only scope); `issue.post_answer`
  (script/push).
- **Invariants** — agent steps ground claims in fetched text/code (governed
  runtime); `issue.post_answer` double-gated (**C5**). `_issue_agent_step` is the
  factory; `agent.*` handlers registered imperatively.

## `steps/report.py`

- **Steps** — `report.final_summary` (report/report): write `RUN_REPORT.md` from
  accumulated step outputs. Pure output; no failure paths.

## `steps/profile.py`

- **Steps** (8) — see [06-profiles.md](06-profiles.md) §pipeline. Establishment
  (`profile.fingerprint`/`structure_scan`/`ingest_docs`/`agent.profile_repo`) +
  Stage-4 (`profile.detect_drift`/`decay_stale`/`agent.profile_consolidate`/
  `profile.judge`). `risk = knowledge` for the write-capable ones; the judge is
  read-only.

## `steps/rebase_native.py`

- **Steps** (9) — `rebase.prelude`, `phase1..phase5`, `phase2_prepare`,
  `module_rebase`, `phase2_finalize`, `compare_with_locked`.
- **Responsibility** — the candidate native decomposition of the nightly,
  importing the parent's own phase wrappers + `node_rebase_module`.
- **Invariants** — invisible to the planner (candidate playbook only); `_RUNTIME`
  is the per-process memoized parent runtime (re-exported by the shim so test
  fixtures can clear it); phase-4 push is behind the copilot push guard; env
  export is traced (`env_exported`). Names the parent package (allowed literal).
- **Tests** — `test_rebase_native.py`.
