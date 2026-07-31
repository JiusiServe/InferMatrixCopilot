# Merge vllm-omni-rebase-agent into InferMatrixCopilot (repo-rebase v3, no external runs)

**Revision 8 — FINAL.** Seven GPT-5.6 Sol gate reviews (all REVISE; history in
`floofy-squishing-squirrel-reviews.md`). Every correctness finding is resolved below; the
reviewer's two persisting structural asks (OS sandbox, vendor-first staging) are settled
in the Decision Record by the owner. Owner adopted all recommended settings on 2026-07-28.

## Context

`repo-rebase` currently delegates to the external `omni-rebase-orchestrator` subprocess
(`vllm-omni-rebase-agent`, LangGraph 5-phase). Goal: eliminate external runs; absorb the
machinery into the copilot, preserving functionality and performance. No live consumer
(user-attested + PR6 preflight evidence: local scheduler checks, 30-day Buildkite
unattributed-build query). **Canonical external checkout:
`/data/zhoutaichang/rebase/vllm-omni-rebase-agent`** (the deployed instance `.env` points
at); the `copilot/` clone is a working copy only. Baseline run, EXT1, and archival target
the canonical checkout.

**Locked decisions:** (1) full merge, external repo retired; (2) copilot executor
substrate, LangGraph dropped, sub-step resume preserved; (3) full shell→Python port;
(4) direct cutover after validation; (5) offline golden-parity suite + one supervised real
full rebase run; (6) data-first knowledge, minimal adapter code.

### Decision record (owner-settled 2026-07-28, all per recommendation)

1. **Unsupervised agent-mutation runs**: permitted under a **recorded risk acceptance in
   the RUNBOOK** (covers `local_ci` and `full` — any unsupervised run executing agent
   code; `report_only` runs no agents). Exposure is unchanged from the parent; the
   sign-off makes it explicit. OS sandboxing remains future hardening.
2. **Push gate**: phase-3 **test assertion failures pass through flagged** (parent-parity
   CI-feedback workflow); structural failures block (§2.3). `strict_push_gate` available.
3. **Precedence**: `strict_push_gate=true` + `push_with_failures=true` together ⇒ BLOCKED
   with an explanatory message (narrowing beats widening; conflicting intent is refused).
4. **Exit codes**: **reuse `blocked`/exit 3** for every needs-human terminal state; no new
   exit code, no consumer-set changes (§3.1).
5. **External-takeover dual-write: dropped.** No ParentStateFile, no takeover drill, no
   parent-format compatibility claim. Rollback = the selectable v1 backend or a fresh
   external run (§3.3).
6. **PR4d (knowledge migration + env-bridge deletion) deferred until after live
   validation** — old stores keep working through cutover; less simultaneous change.
7. **Staged enablement accepted** with the objective thresholds in §9.1.
8. **Vendor-first staging stays rejected** (compensating control: selectable v1 backend).
9. **One supervised live validation run** + staged soak (~7 live data points) — no larger
   live campaign.
10. **`ci_e2e` external takeover not claimed**; mid-CI crashes are copilot-resume or
    manual runbook.
11. **Main-gate single-occupancy enabled** for vllm-omni (dedicated gate pipeline,
    parent parity, scoped + logged).
12. **Canonical checkout** as above.

## 1. Target architecture

### 1.1 Package layout

```
src/infermatrix_copilot/
  rebase_engine/            # NEW, repo-neutral, zero repo literals
    runctx.py               # RebaseRuntime (run-scoped resource owner, §3.4)
    substate.py  state.py  agent_loop.py  tools/  prompt_builder.py  routing.py
    test_manifest.py  test_loop.py  ci_loop.py  phase1_steps.py  module_rebase.py
    report.py  regression_triage.py  debug/  lib/
  testing/  ci/buildkite_monitor.py  memory/curator.py  adapters/hooks.py
  engine/steps/rebase_native.py   # v3 step set; v1 preserved as repo-rebase-native-v1

adapters/vllm_omni/         # SEED data only — committed, human-promoted
  manifest.yaml  hooks.py  prompts/*.tmpl  testing/  rebase/  skills/

~/.infermatrix-copilot/state/vllm-omni/   # RUNTIME mutable state
  debug_memory.db  skills_runtime/  watchdog_overlay.yaml  watchdog_decisions.jsonl
  locks/  upstream_scratch/  backups/
```

Seed/runtime split: adapter tree read-only at run time; loaders merge seed + runtime
(runtime wins collisions; intra-layer duplicates are load errors). Deployment-time
transactional migration (PR4d, post-validation) with seed-only fallback + `capability_gap`
trace. Knowledge rollback is non-destructive: move to `backups/<ts>/`, restore = move
back. sqlite WAL + flock. Report-only mode opens stores strictly read-only.

### 1.2 Prior-knowledge taxonomy (data-first)

Structural facts → `manifest.yaml` (single source; parent's authoritative module paths
copied in — adapter zero's have drifted; kills the 4-way duplication across config.py /
config.sh §11 / prompts/builder.py / test_manifest.py). Prompt domain knowledge →
`prompts/*.tmpl` + `domain_hints`; neutral scaffolding in `prompt_builder.py`;
byte-identical renders (golden-tested). Behavioral policies → `hooks.py` implementing
`RebaseHooks` (neutral base with working defaults; loaded only for declared + `active`
adapters; `HIGH_RISK_SECTIONS` gains `"hooks"`). Learned knowledge → runtime dir only.
`test_repo_neutral_core` keeps scanning `src/`; new packages land with zero leaks.

## 2. Playbook `repo-rebase` v3 (candidate until validated)

Params (defaults explicit): `rebase_mode` (unset ⇒ `report_only`), `main_ci_idx` (0),
`halt_on_module_failure` (false), `halt_on_phase3_failures` (false), `push_with_failures`
(false), `strict_push_gate` (false). Conflicting `strict_push_gate`+`push_with_failures`
⇒ BLOCKED (Decision 3). `requires: [modules, upstream.fork_tracking, ci.provider]`;
`PlaybookStore.find` enforces `requires ⊆ capabilities` for exact-repo matches (verified
no-op for existing playbooks) **and `missing_capabilities()` is updated to report gaps
for exact-repo playbooks too**; prelude re-validates.

### 2.1 Rebase-mode contract — one authority, reflected into governance

`TaskSpec.report_only` keeps its global type (bool). For `repo_rebase`, the only
authoritative mode source is `params.rebase_mode`; **`full` can only ever be selected
explicitly** — no omission or boolean reaches it.

Truth table (`spec.report_only` × `rebase_mode`):

| spec.report_only | unset | =report_only | =full | =local_ci | =remote_ci |
|---|---|---|---|---|---|
| false (default/explicit — indistinguishable, treated identically) | **report_only** | report_only | full | local_ci | remote_ci |
| true (explicit phrasing only) | report_only | report_only | BLOCKED | BLOCKED | BLOCKED |

`resolve_effective_mode(spec, playbook)` runs in `Copilot.run_task`/`run_playbook` after
planner resolution, **before plan-only echo and `_gate_and_confirm`**. It writes the
canonical mode to `spec.params["rebase_mode"]` **and writes back
`spec.report_only = (mode == report_only)`** — so every existing `TaskSpec`-derived
consumer (its `read_only`/`confirm_required` properties, confirmation text, tracing,
metrics, the runner's skill-touch suppression, push-policy construction, finalization)
sees the same truth with no second authority. Audited consumer list is part of the test.
Persisted in `task.json`; seeded into state as `mode_*` flags by `_execute`; `--resume`
restores from `task.json`; prelude validates state ≡ task.json; `when:` gates use only
`mode_*`/`phase3_halt`/`push_gate_*`/`wave2_modules` (hygiene test). Path tests: CLI,
intent (sets `report_only` only on explicit phrasing), chat, plan-only, confirmation,
persistence, resume, MCP-refusal.

### 2.2 Per-mode execution matrix (steps + preconditions)

| Mode | Steps run | Preconditions (validated by prelude, else BLOCKED) |
|---|---|---|
| `report_only` | prelude → guard(check-only) → scan → report | adapter active; stores readable |
| `full` | entire pipeline (§ below) | clean trees; upstream reachable |
| `local_ci` | prelude → guard → phase3_tests → phase3_precommit → push_gate(vacuous) → phase4_ci(local-only) → reports | **operates on the current prepared tree** (fresh-run allowed): clean committed tree; test manifest present (rebuilt by prelude if missing); wheel pin present in `docker/Dockerfile.ci` |
| `remote_ci` | prelude → guard → push_gate → phase4_ci(push+monitor) → reports | committed clean tree ready to push: wheel pin present, `vllm_commit` signal/substate present; `ALLOW_PUSH=1` else FORBIDDEN at phase4 |

Full pipeline order:

```
prelude → guard → [scan] → phase1_baseline → phase1_merge → phase1_analysis
→ phase2_prepare → wave1 (foreach) → wave_gate → wave2 (foreach) → phase2_finalize
→ review.patch_gate(pre_push) → phase3_tests → phase3_precommit → push_gate
→ phase4_ci → phase5_report → curate → compare_with_locked → report.final_summary
```

Module failures are substate data (parent parity): step ok with
`modules.<m>.status=failed`; `wave_gate` always runs, empties `wave2_modules` on wave-1
failure; pipeline proceeds; terminal status per §3.1. `halt_on_module_failure=true` ⇒
ESCALATE instead. Warning aggregation is substate-authoritative (written under the
substate lock; `state` carries no warnings).

### 2.3 `rebase.push_gate` — fail-closed on structural failure

Deterministic/read step before `phase4_ci`, computing from substate with an explicit
**failure taxonomy**:

- **Structural failures — always block the push** (unless `push_with_failures=true`,
  explicit and logged): failed modules; red precommit; and phase-3 **infrastructure
  failures** — harness crashes, timeouts, missing dependencies, corrupt/empty manifest,
  agent dispatch failures. These are never classified as ordinary test failures
  (`test_loop` already distinguishes rc/timeout/skip classes; the taxonomy maps them).
- **Test assertion failures — pass through flagged** (Decision 2); `strict_push_gate=true`
  makes them blocking.
- Blocking ⇒ step returns FORBIDDEN ⇒ run terminal per §3.1 row 3. Vacuous in
  `report_only`/`local_ci`.
Pins: `test_push_gate_blocks_structural`, `test_push_gate_taxonomy_infra_vs_assert`,
`test_push_gate_strict`, `test_push_gate_conflicting_params_blocked`.

## 3. Resume, crash consistency, run lifecycle

Durable atomic writes (tmp + fsync(file) + replace + fsync(dir)) for `progress.json`,
substate, and CI operation records. Same-run flock on `<run_dir>/.lock`.

**Cross-store recovery matrix** (ordering + idempotency; each row a pinned test):
substate-first write order; substate written / progress missing ⇒ step re-enters,
substate short-circuits make it idempotent; progress present / substate stale (guarded
impossible) ⇒ substate authoritative, step re-entered; push accepted / record incomplete ⇒
§3.2 WAL reconciliation; finalizer ran / status missing ⇒ finalizer idempotent,
re-derives.

### 3.1 Terminal-state transition table (authoritative)

One table covers step result → executor outcome → finalized status → report → exit code
(Decision 4: exit 3 = the single needs-human code, as today):

| # | Condition | Executor outcome | Finalized status | Artifacts | Exit |
|---|---|---|---|---|---|
| 1 | all steps ok, substate clean | done | done | RUN_REPORT | 0 |
| 2 | all steps ok, substate has failed modules/tests | done | **needs_human** (reported status; process exits via blocked semantics) | RUN_REPORT + ESCALATION | **3** |
| 3 | push_gate FORBIDDEN / any step BLOCKED/ESCALATE/FORBIDDEN | blocked | blocked (finalizer augments artifacts, never upgrades) | RUN_REPORT + ESCALATION | 3 |
| 4 | non-typed step failure | failed | failed | RUN_REPORT + DIAGNOSTICS | 1 |
| 5 | exception/cancellation/signal | failed/aborted | aborted (finalizer never upgrades) | partial report + `aborted` substate marker | 130/1 |

Finalization is orchestration-level: `_execute` runs `asyncio.run(_run_guarded(...))`;
`_run_guarded` awaits the executor then `finally:` awaits
`runtime.finalize_and_teardown(outcome_or_none)` **shielded** (`asyncio.shield`) so a
second cancellation cannot interrupt cleanup, inside the same event loop; the outer sync
`finally` does last-resort lock release only. The finalizer derives from substate + trace
(resume-stable, idempotent with `report.final_summary`). Pins:
`test_transition_table` (parameterized over rows), `test_finalizer_never_upgrades`,
`test_finalizer_idempotent`, `test_shielded_teardown`.

### 3.2 CI mutations and pushes: write-ahead logged, exactly reconcilable

**Builds**: all creation (gate, initial, retries, rebuilds) via
`create_build_guarded(purpose, round)`: durable `{op_id, state: intent}` before the API
call; `build_id` after; `meta_data.imx_op_id`/`imx_run_id` on the build. Recovery: exact
`imx_op_id` match; zero matches ⇒ bounded eventual-consistency re-poll (3× over ~3 min)
then ESCALATE; multiple ⇒ ESCALATE; never re-create on uncertainty.
Pipeline+branch+commit matching only for the non-crash webhook-adoption flow
(adopted = monitor-only). Cancellation/rebuild only for op-recorded builds; main-gate
single-occupancy per Decision 11. `BUILD_NO_RUN_STATES` kept.

**Pushes are write-ahead logged**: before any `git push`, persist durably
`{branch, remote_pre_push_oid | ABSENT, intended_oid, state: intent}`; after acceptance,
mark `state: pushed`. Crash between ⇒ re-entry reconciles by reading the remote OID:
remote == intended ⇒ mark pushed; remote == pre-push ⇒ retry; anything else ⇒ ESCALATE.
RUNBOOK rollback = reverse-order over the log; `ABSENT` branches roll back by
lease-protected deletion. Crash tests per surface.

### 3.3 Rollback story (dual-write dropped — Decision 5)

No parent-format compatibility layer exists. Rollback paths, all rehearsed:
- **Pre-cutover / mid-soak**: run `repo-rebase-native-v1` (selectable backend, imports the
  unmodified parent in-process) or a fresh external run from the canonical checkout.
- **Mid-run failure**: copilot `--resume` (the only resume authority — simpler than the
  two-authority world this replaces).
- **EXT1** (external repo, before PR6): startup flock on `locks/omni.lock` so external and
  copilot runs cannot share the checkout; pinned SHA; independently revertible.
- **Cutover abort criteria** (objective, in the RUNBOOK): validation gate fails; >25 %
  end-to-end wall-clock regression; any unowned CI mutation observed; lock leak; any
  ESCALATION during soak stages 1–2. **Rollback is rehearsed once before PR6** (timed;
  target < 30 min from decision to v1 backend running).

### 3.4 Run-resource lifecycle

`RuntimeRegistry` keyed by `(run_dir, event-loop id)` with a `threading.Lock` —
runtimes are **loop-scoped**, so `asyncio` primitives inside never cross `asyncio.run`
boundaries; repeated sequential runs/chat invocations pinned by test. Double-checked
`get_or_create`; concurrent handler entry awaits a per-runtime `asyncio.Event` (same
loop by construction). Owns: run-dir flock, checkout flocks (`locks/omni.lock`,
`locks/upstream.lock`), upstream scratch clone, env plans, substate handle, stores,
abort state, finalizer registration. Teardown inside `_run_guarded`'s shielded finally,
60 s timeout, last-resort sync cleanup outside. Signal contract: handlers only set the
abort flag + cancel the task; cleanup (killpg of test process groups, cancel op-recorded
builds, `aborted` marker) in async teardown; second signal ⇒ best-effort killpg +
immediate exit; init-cancellation cleans partial resources. Abort tests with a fake
runtime.

## 4. Agent loop

Port `_run_agent_loop` as `agent_loop.py`; steps stay `kind=script`; not migrating to
`agent_runtime` (prompt bytes, mandatory streaming at 32k max_tokens + tool-input
accumulation, plan gate via `.decision.md`, 150-turn budget). 20 ToolDefs via
`tools.dispatch(..., extra=...)` with the **opt-in** scoping extension (only ToolDefs
declaring `write_path_arg`; zero behavior change for existing steps).

**Risk reduction, no containment claim** (the Decision-1 recorded risk acceptance is the
control for unsupervised agent-mutation runs): per-run disposable `git clone --shared`
scratch upstream for agents (accident prevention); credential scrub in the shell child
env (`ANTHROPIC_*`, `OPENAI_*`, `CURSOR_*`, `BUILDKITE_API_TOKEN`,
`GITHUB_TOKEN`/`GH_TOKEN`, SMTP/Resend, askpass; `HF_TOKEN` retained only when the
manifest declares `validation.requires_hf_token: true`); git env-config pushurl friction
(documented bypassable); attempt-scoped omni snapshot/restore (parent machinery). Named
residual risks: same-user host execution; SSH/cloud/filesystem credentials; `gh` auth.

Model/backend via `Settings.tier_target(mode)`; served-model guard on
`get_final_message().model`; StagedSideEffects via ContextVar; plan review rebuilt on the
copilot LLM client (`Settings.rebase_reviewer_model`), soft-fallback preserved.
**Request-shape golden** (cache compatibility): fake-client test asserts serialized
payload identity (system placement, message segmentation, tool-schema order, adjacency,
max_tokens, model id) vs the parent's recorded payload.

## 5. Knowledge stores

Skills seed adapter-side (28 migrated + existing), counters/candidates runtime-side;
retrieval = seed ∪ runtime; prompt-rendering parity. `skill_manage(create)`
verification-gated (StagedSideEffects commit after FULL_JOB-green re-run) into
`skills_runtime/`, surfaced via `PROMOTION.md`, `knowledge_write` trace; unverified
attempts write nothing. Debug memory runtime-side (copilot schema + additive columns:
`key`, `tags`, `watch_outs`, `upstream_commit`, `last_seen_run`, `source`).
**Migration runs in PR4d, after live validation** (Decision 6): transactional, temp dir +
atomic rename, `MIGRATION_REPORT.md`, dedup `(module,key)` then Jaccard ≥ 0.8; until
then the engine reads the parent's existing stores read-compatibly. Curator pre-flight in
`phase2_prepare`, full curate in `rebase.curate` (knowledge risk, runtime stores only);
watchdog learning appends to the overlay YAML.

## 6. Config & env

`Settings.rebase:` (prefix `REBASE_`) for neutral knobs (`test_timeout_sec=7200` default —
kills the env-force hack; retries; `agent_max_turns=150`; plan-review knobs; CI retry
counts). Manifest holds repo specifics (`push.signoff`, `repo.venv`, pipelines, wheel
variant, baseline-discovery regex, module maps, artifact globs,
`main_gate_single_occupancy: true`, `validation.requires_hf_token: true`). `.env`: keys +
machine paths. `AGENT_CMD_*`/L1–L4 die with the CLI agents; remote-exec not ported
(capability_gap). `_export_all_settings` deleted (in PR4d); child env =
inherit-plus-overlay (`os.environ.copy()` + venv PATH/VIRTUAL_ENV, `CUDA_VISIBLE_DEVICES`,
`HF_HOME`, per-job pairs, main-baseline `PYTHONPATH`; explicit `baseline=True`); agent
shell additionally applies the scrub + env-config. Our process env is never mutated
(guardrail test). Hidden `os.environ` readers (`AGENT_MODEL`, `REBASE_RUN_ID`,
`REBASE_VLLM_COMMIT`, `REBASE_VENV`, `LOG_DIR`, …) become explicit parameters;
`STATE_WRITES_DISABLED`/`PHASE3_SKIP_CLI_DEBUG` vanish.

## 7. Shell-to-Python port

~12 live scripts ported; superseded rest dropped (36/93* → test_manifest/monitor.py;
30/42/45/99 → existing Python; plan-review daemon; claude_auth/tmux/retry wrappers;
remote_exec; `config.sh` + `00_env.sh` die). Load-bearing: **test-runner cluster** →
`src/infermatrix_copilot/testing/` (timeout layering: primary timer kills the process
group at `job.timeout_sec`, watchdog may kill earlier, +900 s safety strictly later —
pinned; `.prev` backups; silent-exit postmortem footers incl. rc=4/5; cov-strip fallback;
`.passed_<slug>` markers; `_main_baseline` suffix; artifact cleanup; model-download email
hook; watchdog two-tier seed+overlay patterns, bash-ERE→`re` with per-pattern fixtures,
eco-tier Tier-2 review, 90 s cap, default-CONTINUE; GPU lock byte-compatible on-disk
protocol; `imx-omni-pytest` ships PR1, referenced only by the new PR4b templates).
**Push cluster** → `push_to_ci.py` + neutral `gitio.py`; `PushPolicy.lease_expect`
(SHA-pinned `--force-with-lease=<branch>:<sha>`); clean-env push execution in the caller.
**Wheel picker** → `wheel.py` (exact walk order; injectable index probe; install retries;
`_C_stable_libtorch` import-check constants; byte-parity pin edits). **Guard** → extended
`workspace.guard_clean` (stale merge-state abort neutral; artifact globs from manifest;
L2 dirty-worktree decision as an agent step, same JSON schema). `35/40/41` → adapter
`rebase/` modules; path-sync retargets the manifest module map.

**Pre-existing false-pass bug** (manifest slug missing from config.sh §10 → empty command
→ rc=0): surfaced by shell-golden into `DRIFT_TRIAGE.md`, decided before cutover.

## 8. Golden-parity harness

Offline conventions; fixtures from the canonical checkout's recorded run
(`rebase_logs/runs/rebase-20260725-144147/`, sanitized).
1. **Byte parity**: Dockerfile pins, commit messages, signals, watchdog markers/footers,
   unstage sets, golden prompts, golden request payloads.
2. **Behavioral replay**: watchdog verdicts on recorded logs; silent-footer
   classification; state accounting; promotion-rule replay.
3. **Command-echo**: `run_test_job(dry_run=True)` vs `shell_golden.json` (one-time GPU-box
   `declare -p` capture of §10 arrays + module maps + watchdog arrays).
4. **Invariant units**: timeout ordering + 900 s; GPU-lock compat; default-CONTINUE;
   substate merge/stamp; wave gate; serialized CI debug; ALLOW_PUSH grep (orchestration);
   no-env-mutation; mode truth table + when-key hygiene + governance write-back audit;
   per-mode precondition matrix; push-gate taxonomy + conflict block; transition table;
   recovery matrix; push WAL reconciliation; build op-id recovery + re-poll; loop-scoped
   registry; shielded teardown + abort + second-signal; scratch-clone teardown; versioned
   backups; `missing_capabilities` exact-repo reporting; report-only read-only stores.
Plus the ported parent suite (`test_resume_granularity`, `test_state_persist`,
`test_main_ci_gate_state`, `test_buildkite_cancel`, `test_debug_loop_hardening`,
`test_test_manifest`, `test_phase3_helpers`, …); copilot's ~400 tests stay green —
untouched playbooks' tests are the shared-component regression net.

## 9. Delivery sequence

- **PR0 — executor lifecycle, behavior-preserving**: durable `progress.json` writes,
  run-dir lock, finalizer/teardown hook points (default no-op) — landed with unchanged
  behavior for every existing playbook (no exit-code changes; Decision 4).
- **PR1** testing substrate + `imx-omni-pytest` + parity tiers 2–4 + shell_golden +
  DRIFT_TRIAGE.
- **PR2** phase-1 cluster (standalone modules + parity tests).
- **PR3** push cluster (`gitio.py`, `push_to_ci.py`, `lease_expect`, push WAL).
- **PR4a** engine core, unwired: agent loop, ToolDefs + opt-in dispatch extension,
  substate, `RuntimeRegistry` (loop-scoped), planner `requires` filter +
  `missing_capabilities` update — unit-tested against fakes.
- **PR4b** adapter knowledge: hooks base + vllm-omni hooks, manifest extension, prompt
  templates + prompt/payload goldens, `phase1_steps.py`, `module_rebase.py`.
- **PR4c** assembly: test/ci loops, v3 step set incl. `push_gate` + playbook (candidate),
  `resolve_effective_mode` + governance write-back + ingress audits, transition-table
  wiring, mode/matrix tests, v1 re-registered as `repo-rebase-native-v1`. Engine reads
  parent stores read-compatibly (migration deferred).
- **PR5** parity completion: tier-1 goldens, drift triage resolved, report-only dry path,
  rollback rehearsal (timed).
- **EXT1** (canonical external checkout, before PR6): startup checkout-lock guard; pinned
  SHA in RUNBOOK; independently revertible.
- **PR6** cutover: preflight evidence; §9.1 validation; on pass: v3 → locked
  `repo-rebase`, delegating yaml retired, CLAUDE.md updated; `.env` armed manually
  (timestamped backup of the managed block; `--dry-run` removal is the deliberate arming
  step).
- **PR4d** (post-validation, pre-PR7): knowledge migration + runtime-dir cutover +
  `_export_all_settings` deletion + env guardrail.
- **PR7** retirement after staged soak: delete `rebase_ext.py`/`rebase.run_external`,
  `_FLAG_WHITELIST`, `orchestrator.external`, v1 playbook,
  `Settings.rebase_orchestrator_cmd`/`rebase_agent_root`; tag + archive the canonical
  external repo (README pointer).

**Rollback/abort inventory** (RUNBOOK): playbook flip → revert; `.env` → restore backup;
running CI → cancel op-recorded builds; pushed refs → reverse-order WAL restore incl.
created-branch deletion; validation branches → deleted post-freeze; mutated omni checkout
→ snapshot restore or manual steps; upstream → scratch discarded; runtime knowledge →
versioned backup restore; EXT1 → external revert. Abort criteria + rehearsed < 30 min
bound per §3.3.

### 9.1 Validation and staged enablement

Controlled comparison: frozen `(omni_sha, vllm_sha)` via `FORCE_VLLM_COMMIT`; knowledge
snapshots restored before each run; pinned model ids/templates/tool schemas (RUNBOOK);
isolated clones; separate validation branches (`rebase-val-ext-<date>` /
`rebase-val-nat-<date>`); one external baseline run to `phase=done` from the canonical
checkout (none exists — latest recording is mid-flight); one supervised v3 full run
(`ALLOW_PUSH=1` deliberate, human attached). Gate: deterministic harness green (primary
evidence) + live outcome equivalence (identical slug set; per-module/per-slug
equal-or-better, one-rerun flaky protocol; CI equal-or-better; push/commit shape
identical) + 25 % wall-clock coarse sanity bound + human-signed COMPARISON.md;
divergences investigated via the v1 backend, never averaged away.

**Staged enablement** (Decision 7; regression at any stage falls back one stage + opens
an investigation):
1. `report_only` nightly, unsupervised: promote after **3 consecutive clean runs** (exit
   0, no lock leaks via post-run lock-dir scan, no ESCALATION.md) **with deterministic
   outputs — manifest, drift scan, assignment preview — diffed against a frozen baseline
   each run** (semantic, not just crash-free).
2. `local_ci`, unsupervised (covered by the Decision-1 risk acceptance): promote after
   **2 consecutive runs with zero new DRIFT/parity items** and outcome sets matching
   stage-1 expectations.
3. Push-capable `full`, unsupervised: allowed under the same recorded risk acceptance
   after **2 supervised clean full runs**.
Total live evidence before PR7: baseline + validation + ≥5 staged runs, with v1 and the
external path available throughout.

## 10. Invariant preservation (condensed)

Phase marker at completion (executor checkpoints on ok; ported resume tests) ·
run_id-stamped per-run-dir substate · `slugify` ≡ manifest slug (single function) ·
serialized CI debug · staged side effects / verification tiers / tolerance gate ·
streaming loop + request-shape golden · single-writer state + durable writes + locks ·
wave gating · BUILD_NO_RUN terminal + op-id ownership + fail-closed trigger + push WAL ·
attempt-scoped diffs · repo-neutral core (ceiling frozen) · push gates (guard_push +
grep pin; agent shell scrub + env-config) · prompt/cache parity goldens · main-CI gate
rehydration · mode truth table + governance write-back + per-mode matrix · transition
table rows · adapter tree read-only at run time · loop-scoped runtime reacquisition ·
versioned knowledge backups · PR0 behavior preservation.

## 11. Top risks & mitigations

1. Dual command source false-pass — shell-golden + DRIFT_TRIAGE.
2. Watchdog regex translation — per-pattern fixtures.
3. Timeout layering — ordering test + 900 s margin.
4. CI/push crash windows — op-id gateway + push WAL, exact reconciliation, fail-closed
   escalation, crash tests.
5. Failed work reaching remote — push_gate taxonomy (structural fail-closed) +
   transition-table terminal contract.
6. Watchdog model swap — pre-LLM filters, default-CONTINUE, decision diff.
7. `run_shell` — risk reduction only; Decision-1 recorded acceptance; named residual
   risks; OS sandbox deferred.
8. Shared-component regressions — PR0 behavior-preserving, additive/opt-in changes,
   existing playbook tests, PR granularity.
9. Validation sample size — deterministic harness primary; staged semantic thresholds;
   ≥7 live points before retirement.
10. Concurrency & lifecycle — run/checkout locks, EXT1 enforcement, loop-scoped registry,
    shielded teardown, abort contract, recovery matrix.

## Verification

Offline: copilot suite + ported parent suite + parity tiers 1–4 green (incl. truth table,
governance write-back, per-mode matrix, push-gate taxonomy, transition table, recovery
matrix, push WAL, re-poll, loop-scoped registry, shielded teardown, backups); report-only
dry path; doctor green. Live: §9.1 validation with human-signed COMPARISON.md; timed
rollback rehearsal; staged soak per thresholds before retirement.

## Critical files

Copilot: `engine/steps/rebase_native.py`, `engine/executor.py` (PR0), `cli/copilot.py`
(`resolve_effective_mode`, `_run_guarded`, signal contract), `playbooks/store.py`
(requires filter + `missing_capabilities`), `tools.py` (opt-in scoping), `push.py`
(`lease_expect`), `adapters/base.py` (hooks loading), `config.py`,
`playbooks/repo-rebase*.yaml`, tests. Parent sources: `agent/nodes/phase2_rebase.py`,
`agent/subgraphs/phase3.py`, `phase4.py`, `agent/nodes/phase1_init.py`,
`agent/lib/test_runner.sh`, `test_watchdog.sh`, `agent/tasks/92_push_to_ci.sh`,
`10_pick_wheel_commit.sh`, `agent/buildkite/monitor.py`, `agent/test_manifest.py`,
`agent/debug/*`, `agent/curator.py`.

## Review-history note

Seven reviewer iterations shaped this plan (see `floofy-squishing-squirrel-reviews.md`).
Residual reviewer positions **not** adopted, by owner decision: OS sandboxing as a
precondition (→ recorded risk acceptance instead); vendor-first staging (→ selectable v1
backend); larger live-validation campaign (→ one supervised run + staged soak). All other
findings across iterations 1–7 are incorporated or explicitly superseded by later,
simpler reviewer suggestions (exit-code reuse, dual-write removal).
