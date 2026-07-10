# Code tour — reading guide for vllm-omni-copilot

A guided path through the codebase (v1 engine + the Design-v2 work: repo
invariance and repo profiles). Written for reviewing the code, so it follows
*execution order*, names the invariants each file enforces, and points at the
test that pins each behavior. Companion docs: `DESIGN.md` (why),
`IMPLEMENTATION_STATUS.md` (what's done).

## 0. Orientation: one task, end to end

Take `omni-copilot -p "review pr 4830"` and follow it:

```
cli.py:main            parse flags; one-shot -p / chat / REPL
  intent.py            NL -> TaskSpec        (deterministic first, LLM fallback)
  task_spec.py         TaskSpec: kind/pr/flags; TIER DERIVED FROM KIND
  cli.py:Copilot.resolve
    plugins/base.py    RepoPlugin.capabilities (repo.path, ci.provider, ...)
    engine/planner.py  reuse > adapt > generate  (+ capability matching)
      playbooks/store.py  registry: candidate/active/locked; find()
  cli.py:run_task      echo plan; plan-review gate; [y/N] confirm
  engine/executor.py   run steps: checkpoint/resume, foreach, when:, retries
    engine/builtin_steps.py   the step handlers (incl. agent.review_diff)
      engine/agent_runtime.py governed agent execution (the heart)
        agent_loop.py        the raw tool loop
        tools.py + scopes.py the single scope-enforcing dispatcher
  notify.py            ESCALATION.md + email + exit 3 when blocked
  metrics.py           CATQ metrics.json per run
```

Suggested reading order = the sections below, top to bottom.

## 1. Task layer — how words become a governed task

- **`task_spec.py`** (~70 lines, read fully). The one invariant that matters:
  `tier` is a *property of the kind* — there is no field an LLM or user could
  set to widen permissions. `read_only`/`confirm_required` derive from kind +
  flags. v2 added the `repo_profile` kind (L2, confirm-gated because it
  writes knowledge).
- **`intent.py`**. Deterministic keyword parser first (`_KIND_HINTS` + PR/issue
  regexes), LLM parse only as fallback, and *ambiguity always becomes a
  clarifying question* — never a guessed execution. Note the guards: a
  `pr_*` kind without a PR number never matches; `repo_*` kinds refuse when a
  PR is present. Only terminal input reaches this function — fetched GitHub
  text never does (prompt-injection channel separation).
  Pinned by `test/test_intent_taskspec.py`, `test_profile_steps.py::test_intent_parses_profile_command`.

## 2. Planning — reuse > adapt > generate, now capability-matched

- **`playbooks/store.py`**. `Playbook` is data (yaml in `playbooks/`), with
  `status` ∈ candidate/active/locked/retired. Key methods:
  - `find(kind, repo, capabilities)` — exact-repo playbooks win; repo-neutral
    ones (`repos: []`) match only when `requires ⊆ capabilities`
    (v2 P2.1; `capabilities=None` = v1 behavior). Candidates are *never*
    recalled — only `--playbook <name>` runs them.
  - `missing_capabilities()` — escalation material for gaps.
- **`engine/planner.py`** (~120 lines, read fully). The three-way resolution
  and its two hard rules: locked playbooks refuse adaptation; the generate
  path is *structurally* barred from write/push steps and exists only for
  read-only kinds. v2 added the capability-gap branch: a write-capable kind
  whose repo profile can't satisfy a vetted playbook raises
  "capability gap … run repo_profile" instead of failing silently.
  Pinned by `test_planner_playbooks.py`, `test_capabilities.py`.
- **`plugins/base.py`**. `RepoPlugin` = the edge where repo knowledge lives:
  manifest (`plugin.yaml`), `module_for_path`, `high_risk_modules`
  (`risk: high` markers), `capabilities` (derived + explicit),
  per-repo `skills_dir`/`debug_memory_db`/`profile_dir`/`briefing()`.
  `update_manifest` rejects agent writes to high-risk sections
  (`push`/`repo`/`upstream`) — that's the human-only wall.
  Phase-0 bootstrap: `fingerprint_repo` (deterministic, no LLM) +
  `draft_plugin` (stops at `status: draft`).

## 3. Execution — the engine substrate

- **`engine/step.py`** (~70 lines, read fully). The vocabulary: `StepSpec`
  (name/kind/risk/handler), `StepResult` (ok + typed `FailureKind`),
  `StepContext` (everything a handler may touch). Six failure kinds route
  differently — that's the whole point.
- **`engine/executor.py`** (~200 lines, read fully). Task-agnostic
  guarantees: per-step checkpoint (`progress.json`), `foreach` fan-out
  (asyncio.gather + `_merge`), `when:` conditions, bounded retries on
  RETRYABLE only, BLOCKED/ESCALATE/FORBIDDEN → notifier + exit.
  **The v2 P0 state contract lives here**: steps publish every state key a
  later step consumes via `outputs.state_updates`; resume restores them;
  `_merge` lifts fan-out updates; `when:` reads TaskSpec then state and
  *blocks loudly* on unknown keys. If you review one v2 fix closely, make it
  this one — the old behavior silently broke every resumed run.
  Pinned by `test_engine.py`, `test_v2_p0.py` (resume-integrity tests).

## 4. The governed agent runtime — the heart

- **`engine/agent_runtime.py`** (read fully; it's the densest file).
  `run_agent_step` is the single entry for every `kind == "agent"` step:
  1. `AgentDispatchContext` — structured input, rendered once: task/step/
     repo/briefing/evidence/permissions/skills/memories/output contract.
     Evidence is fenced in `<untrusted_data>` and *capped per item* with the
     full text archived to the run dir (`_build_evidence`).
  2. Knowledge: `_ScopedKnowledge` (v2 P0) — per-repo skills + debug memory
     consulted before the shared pool; agent proposals land in the repo's
     namespace, candidates only.
  3. `_repo_map_tool` (v2 P2.2) — goal-ranked structure queries on demand;
     never injected as prose.
  4. Output contract (base schema + per-step extension), one repair round,
     typed status → FailureKind mapping; budget exhaustion forces a final
     answer instead of discarding the investigation.
  `run_agent_step_ensemble` below it is the review-quality machinery:
  perspective-diverse lens fan-out, exact-duplicate collapse → consensus,
  per-NUMBERED-candidate keep/drop/dup verdicts assembled deterministically
  (unmentioned = kept, fail-open), consensus-gated fast path. The inline
  comments cite the eval results that forced each choice — read them, they
  are the institutional memory of the optimization campaign.
- **`agent_loop.py`** + **`tools.py`** + **`scopes.py`** (short, read all
  three together). One rule: *every* tool call goes through
  `tools.dispatch`, which checks the `ToolScope`/`PathScope` and traces.
  Three outcomes: allowed / refused / executed-but-recorded (out-of-scope
  write inside the writable wall). Agent steps never see a tool their scope
  doesn't allow. Pinned by `test_scopes_tools.py`, `test_agent_loop.py`.

## 5. The step library — what the playbooks are made of

- **`engine/builtin_steps.py`**. Skim top-to-bottom, stop at:
  - `_run_external_rebase` — the locked nightly: monitored subprocess
    delegation to the parent orchestrator (state.json → progress events,
    stale-state guard, failure classification → escalation artifacts).
  - `_patch_gate` — Conditional Patch Review: cheap diff summary always,
    LLM review only when `review/triggers.py` rules fire (high-risk modules
    now come from the *plugin*, settings is fallback — v2 P0).
  - `_push` — thin: all safety is in `targets/base.py::guard_push`.
  - `_REVIEW_SYSTEM` + `_REVIEW_LENSES` + `_sweep_targets` — the review
    prompt system. v2: repo-neutral core; the domain checklist extends from
    the profile's `review.md`; sweep extractors are keyed on
    `repo.language` and degrade honestly for unknown languages.
- **`engine/pr_steps.py`**. PR rebase (fork-aware checkout → PushPolicy
  derivation → rebase → conflict agent or abort+escalate) and PR debug
  (fetch failing checks → **CI log enrichment** → signature grouping →
  per-group debug agent → additive push). v2 P2.2 wired
  `_enrich_ci_logs` + normalized grouping here.
- **`targets/base.py`** (~80 lines, read fully). `guard_push` is the single
  push choke point: PushPolicy AND protected branches; force is
  with-lease-only and *never* against a protected branch. Everything else
  about push safety is commentary on this function.
- **`engine/rebase_native_steps.py`** — the candidate native decomposition
  of the nightly (imports the parent's own phase wrappers). Only read when
  working on the promotion path.

## 6. Repo profiles (v2) — the knowledge subsystem

Read in this order:

1. **`profiles/store.py`** — the curated layer. Facts with provenance
   (`source`/`evidence`/`first_seen`/`last_confirmed`/`confirmations`),
   typed patch ops as the *only* write surface, two tiers (`RUN_OPS`
   additive; `CONSOLIDATE_OPS` may rewrite/merge/stale), the stability gate
   (stable facts never lose cited evidence; superseded text → `history`),
   merge stubs, and the three consumption channels — `render_briefing()`
   emits *only* briefing-channel facts under a hard word budget. This file
   is the personal-agent architecture transplanted; the docstring says which
   rule guards which failure mode. Pinned by `test_profile_store.py`.
2. **`profiles/establish.py`** — Stage 0–1.5 helpers: the 6-word-shingle
   **redundancy filter** (the ETH-study rule: doc-redundant briefing lines
   are pure cost), directive extraction from AGENTS.md-style files,
   deterministic module scan.
3. **`engine/profile_steps.py`** — the pipeline as steps:
   `profile.fingerprint` → `profile.structure_scan` → `profile.ingest_docs`
   → `agent.profile_repo` (facts must cite evidence or the store rejects
   them; overviews are forbidden outputs), plus the Stage-4 set:
   `profile.detect_drift` / `profile.decay_stale` /
   `agent.profile_consolidate` (LLM proposes ops, the store's gates decide)
   / `profile.judge` (read-only audit; structurally cannot mutate).
   Playbooks: `repo-profile` (active, repo-neutral) and
   `profile-consolidate` (candidate = scheduled/explicit only).
   Pinned by `test_profile_steps.py`, `test_p3_machinery.py`.
4. **`profiles/repo_map.py`** — regex symbol index per language, disk-cached
   by HEAD, query-ranked render under a char budget. The design stance:
   structure is *pulled* by the agent (channel 3), never pushed as an
   overview.
5. **`profiles/consolidate.py`** — decay + drift (deterministic, report-only).

## 7. CI adapters (v2) — `ci/`

- **`ci/normalize.py`** (30 lines, read fully): signatures lose timestamps/
  hashes/addresses/tmp-paths/line-numbers/durations before grouping; small
  literal numbers are kept. This is the deliberate non-inheritance of the
  parent monitor's exact-string-compare bug.
- **`ci/providers.py`**: `provider_for(plugin, settings)` selects by the
  profile's `ci.provider` — `BuildkiteLogs` (REST, per-check best-effort)
  or `GithubActionsLogs` (`gh run view --log-failed`, cached per run).
  Missing provider/token → `(None, reason)` → the step records a
  `capability_gap` event and pr-debug degrades to name grouping.
  Pinned by `test_ci_and_repo_map.py`.

## 8. Safety, memory, surfaces — the rest

- **`review/`**: `diff_summary.py` (cheap always-on facts) →
  `triggers.py` (7 rules) → `reviewer.py` (read-only verdict; anything but
  `lgtm` is not-passing — fail-closed).
- **`run_trace.py`** (40 lines): append-only jsonl; every governance claim
  in this codebase ultimately means "there is a trace event for it".
  Notable events: `agent_dispatch`/`agent_output`, `tool_refused`,
  `out_of_scope_edit`, `capability_gap` (v2), `profile_*` (v2).
- **`memory/`**: `debug_memory.py` (FTS write contract: root_cause +
  verification required) and `skills.py` (propose → candidate → human
  promote).
- **`notify.py`**: ESCALATION.md + email + `BLOCKED_EXIT=3` — "notify,
  never guess" as code.
- **`metrics.py`**: CATQ = Q·S/C per run; never allowed to break a run.
- **`cli.py`** then **`chat.py`**: both funnel into the same
  `run_task`/`run_playbook` — chat is a frontend, not a second execution
  path (its tools can't widen permissions; repo reads are jailed and
  `.env*` refused). `ui.py` is presentation only.

## 9. The guard tests — behaviors you must not break

| Test | The invariant it pins |
|---|---|
| `test_v2_p0.py::test_repo_neutral_core` | repo literals in `src/` capped at the known-leak list (can only shrink) |
| `test_v2_p0.py::test_resume_restores_state_handoffs` / `test_push_policy_survives_resume` | the state_updates contract |
| `test_capabilities.py` | neutral playbooks match by capabilities; locked rebase never leaks to other repos |
| `test_profile_store.py::test_stability_gate_and_history` | stable facts never lose evidence; history never deleted |
| `test_profile_steps.py::test_profile_agent_applies_gated_facts` | evidence-free facts rejected; doc-redundant briefing dropped |
| `test_p3_machinery.py::test_judge_reports_but_never_mutates` | the judge is read-only |
| `test_agent_runtime.py` (parametrized dispatch test) | `kind == "agent"` ⇒ unified-runtime-governed, no ad-hoc LLM calls |
| `test_push_and_steps.py` | guard_push semantics |

## 10. Running things

```bash
pip install -e . && pytest                      # 211 offline tests
omni-copilot -p "review pr 4830" --plan-only    # see a plan without running
omni-copilot -p "profile the repo" --yes        # establish a profile (draft)
omni-copilot --playbook profile-consolidate --yes   # Stage-4 maintenance
PROFILE_BRIEFING_ENABLED=0 ...                  # the {no-profile} eval arm
omni-copilot --resume                           # re-enter the last run
```

Artifacts per run: `~/.omni-copilot/runs/run-<ts>/` (`run_trace.jsonl`,
`progress.json`, `RUN_REPORT.md`, `metrics.json`, `ESCALATION.md` when
blocked). Profiles: `plugins/<repo>/profile/` (`profile.yaml`,
`PROFILE_REPORT.md`, `JUDGE_REPORT.md`, `ops_log.jsonl`).

## 11. Where to start changing things

- New repo → `omni-copilot -p "profile the repo"`, review the draft plugin +
  PROFILE_REPORT, flip `status`, done — zero core edits is the contract.
- New step → implement in an `engine/*_steps.py`, register with an honest
  `risk`, publish consumed state via `state_updates`, add a guard test.
- New task kind → `task_spec.py` (kind + tier) → playbook yaml → intent
  hints → chat enum. The planner and executor need nothing.
- New repo knowledge → a profile fact via typed ops (or a skill), never a
  string in `src/` — `test_repo_neutral_core` will catch you.
