# 07 — Repo Edge: Plugins, Targets, CI, Rebase Monitor

The edge is where repo-specific knowledge and external-system adapters live, so
the core stays repo-neutral (**A5**). Modules: `plugins/base.py`,
`targets/base.py`, `ci/normalize.py`, `ci/providers.py`, `rebase/monitor.py`.

---

## `plugins/base.py`

- **Responsibility** — `RepoPlugin`: repo knowledge at the edge; the plugin
  registry; deterministic Phase-0 bootstrap.
- **Public contract** — `RepoPlugin` (props `status`, `repo_path`,
  `protected_branches`, `modules`, `high_risk_modules`, `capabilities`,
  `skills_dir`, `debug_memory_db`, `profile_dir`, `briefing()`; `module_for_path`);
  `load_plugin`, `update_manifest`, `PluginRegistry(resolve/all)`;
  `fingerprint_repo`, `draft_plugin`.
- **Invariants**
  - **High-risk sections human-only (D2)** — `update_manifest` rejects agent
    writes to `push`/`repo`/`upstream`.
  - `capabilities` derives from the manifest (`repo.path`, `language.*`,
    `ci.provider`, `upstream.*`, `modules`) plus explicit `capabilities:` — this
    is what playbook `requires:` matches against.
  - `high_risk_modules` = modules declared `risk: high` (feeds the patch-review
    trigger; **A5**).
  - `fingerprint_repo` is deterministic, never mutates the target repo;
    `draft_plugin` stops at `status: draft` (human gate).
  - `briefing()` renders the profile's briefing slice (empty when no profile).
- **Scope** — repo identity + knowledge access + bootstrap. No task logic, no LLM.
- **Tests** — `test_plugins.py`, `test_capabilities.py`.

## `plugins/<repo>/plugin.yaml`

- **Contract** — `name, status, repo{path,default_branch,language,…},
  upstream{kind,…}?, modules{<m>{local_paths, wave, risk?}}, validation, ci,
  push{protected_branches, allowed}, capabilities?`.
- **Invariants** — `push.allowed=false` and `protected_branches` are human-gated
  truth; the module map is the join key for knowledge; `risk: high` marks
  high-risk modules. Plugin zero (`vllm_omni`) is the reference.

## `targets/base.py`

- **Responsibility** — target-layer types + the single push guard.
- **Public contract** — `PushPolicy`, `PushDecision`, `guard_push(policy,
  protected_branches)`; plus `ValidationPlan`, `ModuleTask`, `ModuleSchedule`,
  `RebaseRunSpec` (data).
- **Invariants (C4)** — a push happens only when the policy allows it AND the
  branch is not protected; force is with-lease only; a protected branch is never
  pushed to (force or not), regardless of policy. This is the ONLY push
  authorization point; `ci.push`/native phase-4 defer to it.
- **Scope** — push authorization + target data types. No git execution (that is
  the step), no repo knowledge.
- **Tests** — `test_push_and_steps.py`.

## `ci/normalize.py`

- **Responsibility** — normalize a failure signature before grouping.
- **Public contract** — `normalize_signature(signature) -> str`.
- **Invariants** — strips run-varying noise (timestamps, hashes, addresses, tmp
  paths, line numbers, durations) but keeps small literal numbers as signal.
  Deliberate non-inheritance of the parent monitor's exact-string-compare bug —
  the same failure across runs must collapse to one group.
- **Scope** — string normalization only.
- **Tests** — `test_ci_and_repo_map.py`.

## `ci/providers.py`

- **Responsibility** — profile-selected CI log adapters for pr-debug.
- **Public contract** — `provider_for(plugin, settings, gh_runner?) ->
  (provider|None, gap_reason)`; `BuildkiteLogs.enrich`, `GithubActionsLogs.enrich`.
- **Invariants** — provider chosen by `profile.ci.provider`, never hardcoded.
  `enrich` is best-effort **per check** — an API error leaves that check
  name-grouped, never crashes. Missing provider/token → `(None, reason)`, and the
  calling step records a `capability_gap` and degrades to name grouping (**E2**).
- **Scope** — log fetching only. No grouping/debugging logic (that is the step).
- **Extension** — a new CI system → a `*Logs` class + a `provider_for` branch.
- **Tests** — `test_ci_and_repo_map.py`.

## `rebase/monitor.py`

- **Responsibility** — read/classify the parent orchestrator's state for the
  locked `rebase.run_external` delegation.
- **Public contract** — `build_command`, `parse_parent_state`,
  `summarize_progress`, `diff_progress`, `classify_failure`, `build_escalation`.
- **Invariants** — read-only toward the parent's `state.json`; classifies exit
  code + state into a typed failure + escalation material; stale-state aware
  (a previous run's `phase=done` must not mask this run's crash). Names the
  parent package (allowed literal).
- **Scope** — monitoring/classification of the external pipeline. Does not run
  or reimplement the rebase.
- **Tests** — `test_rebase_monitor.py`.
