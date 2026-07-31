# PLAN — Merge `vllm-omni-rebase-agent` into InferMatrixCopilot (repo-rebase v3)

Status: **active migration** on branch `feat/rebase-merge-pr0`. This document
is the as-built successor of plan Revision 8 (7 prior GPT-5.6 Sol design
reviews; owner locked all decisions 2026-07-28). It records what is now BUILT,
what changed against Rev 8 and why, and the remaining delivery sequence.
Update it at every PR boundary.

**Normative scope:** this document supersedes Rev 8 for *status, sequencing,
and recorded deltas*. The detailed execution contracts Rev 8 defines are NOT
restated here and remain normative by reference — Rev 8 is **pinned inside
this repository** as `doc/PLAN-rebase-merge-rev8.md` (immutable historical
copy; any future edit to it is a defect):
§2.1 mode truth table + `resolve_effective_mode` governance write-back,
§2.2 per-mode execution matrix, §2.3 push-gate failure taxonomy,
§3.1 terminal-state transition table, §3.2 CI/push write-ahead logs and exact
reconciliation rules, §3.4 run-resource lifecycle, §8 golden-parity harness
tiers. Where this document and Rev 8 conflict, this document wins; where this
document is silent, Rev 8 governs.

## 1. Goal

Eliminate `repo-rebase`'s external subprocess runs by absorbing the external
5-phase LangGraph orchestrator (`vllm-omni-rebase-agent`) into the copilot,
preserving functionality and performance. Canonical external checkout:
`/data/zhoutaichang/rebase/vllm-omni-rebase-agent` (the `copilot/` clone is a
working copy). No live consumer of the external path exists (user-attested;
**to be re-verified** by the PR6 preflight evidence checks — scheduler scan +
30-day unattributed-Buildkite-build query).

## 2. Locked decisions (owner, 2026-07-28 — unchanged)

1. Full merge; external repo retired at the end (PR7).
2. Copilot-executor substrate; LangGraph dropped; sub-step resume preserved.
3. Full shell→Python port; remote/hybrid execution not ported
   (`capability_gap` traced where it would have been used).
4. Direct cutover after validation (§8); selectable `repo-rebase-native-v1`
   backend is the rollback, ParentStateFile dual-write dropped.
5. Offline golden-parity suite + ONE supervised real full VALIDATION run
   (§8 defines the total supervised-run count across validation + soak: two,
   the validation run counting as the first); staged enablement
   (report_only → local_ci → full) with recorded RUNBOOK risk acceptance for
   unsupervised agent-mutation runs.
6. Data-first knowledge: repo specifics live in `adapters/vllm_omni/`
   (manifest + data files + `hooks.py`); the engine stays repo-neutral
   (`test_repo_neutral_core` ceilings unchanged).
7. Push gate: structural failures block, test assertion failures pass through
   flagged; `strict_push_gate` available; conflicting
   `strict_push_gate`+`push_with_failures` ⇒ BLOCKED.
8. `blocked`/exit 3 reused for every needs-human terminal state.
9. Knowledge migration + runtime-dir cutover (PR4d) deferred until after live
   validation. **Sequencing delta vs Rev 8 (recorded round 3):** the
   env-bridge (`_export_all_settings`) deletion moves from PR4d to **PR7** —
   the v1 rollback backend is its last caller and lives until PR7; deleting
   the bridge at PR4d would break the rollback path before its sunset. After
   PR4d the bridge has exactly one caller (v1); a test pins that.

## 3. Review & delivery protocol (owner, 2026-07-31 — prospective)

This protocol binds **PR2 onward** (it was set mid-PR1: PR0 predates it and
PR1 ran 9 finding rounds before the cap existed, closing with the same
agreement + verification pattern). Every PR must:

- **(a) reach explicit agreement with GPT-5.6 Sol** — an APPROVE verdict —
  within **max 5 finding rounds**, plus a bounded fix-verification cycle:
  **max 2 verification rounds**, where a verification round may surface
  residual defects in the fixes under verification (fixed and re-verified
  once) but any finding OUTSIDE those fixes goes to the owner instead of
  another round. PR2 consumed exactly this budget (5 + 2). Reviews run via
  `cursor-agent --mode ask --model gpt-5.6-sol-high` over the cumulative
  branch diff (prompt via stdin — large diffs exceed ARG_MAX as an argv);
  the ExitPlanMode hook itself times out fail-open, so reviews are
  script-driven, with every round's output archived.
- **(b) include a passing partial-e2e test** exercising the PR's cluster
  end-to-end over fixtures (e.g. `test_phase1_partial_e2e`).
- Every review finding is either fixed with a dedicated regression test in
  the same round, or recorded as an explicit owner position and re-presented
  for agreement (two PR1 positions were accepted by the reviewer this way).

## 4. As-built architecture

```
src/infermatrix_copilot/
  engine/lifecycle.py         # PR0: RunLock, finalizers, run_guarded
  engine/steps/workspace.py   # guard_clean (read) + guard_clean_rebase (write_workspace)
  testing/                    # PR1: gpu_lock, process_tree, watchdog(+learn),
                              #      env_plan, runner  (shell test layer, ported)
  rebase_engine/              # PR2+: repo-neutral rebase machinery
    wheel.py                  #   wheel pick/install + Dockerfile pin (tasks 10/20)
    worktree.py               #   stale-state abort, artifact discard,
                              #   L2 dirty-worktree decision applier (task 01 + lib)
    assign.py                 #   commit→module classification core (task 40)
    path_sync.py              #   path-map sync + manifest retarget (task 35)
    # future: gitio.py, push_to_ci.py (PR3); agent_loop, substate, runctx,
    # test/ci loops, phase1_steps, module_rebase (PR4a–c)

adapters/vllm_omni/           # repo specifics as DATA (+ narrow adapter code)
  manifest.yaml               # modules(local/upstream/test paths) + rebase:
                              #   wheel spec/pin, guard patterns, base-class
                              #   watch list, curated path-sync candidates
  testing/watchdog_patterns.yaml
  rebase/api_drift_guard.py   # standalone script, runs in the TARGET repo env
```

Key mechanisms already landed:

- **Run lifecycle (PR0)**: durable `progress.json` (tmp+fsync+replace+
  dir-fsync, EIO propagates), exclusive same-run lock spanning the reserved-run
  lifecycle incl. MCP children, cancellation-surviving finalizer hook.
- **Process-identity kill safety (PR1/PR2 hardening)** — a guarantee of the
  `kill_tree`/snapshot escalation path specifically: per-pid signalling is
  identity-checked against `/proc/<pid>/stat` starttimes; descendant
  snapshots accumulate `(pid → starttime)` and never shrink; recording and
  ancestry are bound in a single stat read with a fixpoint chain anchored at
  an immutable leader identity; `kill_tree` re-validates roots after the
  descendant walk and `_terminate_tree` delegates the single validated
  expansion to it. Two deliberate NON-identity paths remain: `killpg` on the
  runner's own pre-captured process group (we created that group), and GPU
  orphan cleanup signalling bare device pids (single-tenant lock-holder
  design; recorded, reviewer-accepted owner position). Residual window:
  stat-read-to-signal gap (needs pidfds).
- **GPU serialization**: byte-compatible on-disk lock protocol with the shell
  era; flock-serialized stale-lock steal.
- **Env hygiene (production-wired in PR4c)**:
  `env_plan.build_subprocess_env` (inherit-plus-overlay) drives every
  target-repo subprocess (`_target_test_env`: venv + CUDA + HF_HOME) and
  `scrub_agent_shell_env` applies to AGENT shells only via
  `_agent_shell_env` (scrub + target overlay + the `imx-omni-pytest`
  IMX_* contract; HF token on the manifest's `validation.requires_hf_token`
  opt-in). Child envs are copies; the process env is never mutated.

**Recorded v1-backend exceptions (owner-accepted, sunset = PR7).** The
`repo-rebase-native-v1` backend (today's `repo-rebase-native`, renamed in
PR4c) is the rollback path. Its equivalence boundary, stated precisely: it
executes the PARENT'S OWN phase implementations in-process (the parent
package's test runner, CI monitoring, and phase-4 push semantics), wrapped
in copilot v1 orchestration — it is NOT byte-identical orchestration. Known
v1-vs-parent orchestration divergences, recorded: a pre-push patch gate,
typed copilot retries, and module-failure handling — in v1's DEFAULT mode
(`continue_on_module_failure=false`) both suppress wave 2 on a wave-1
failure, with the parent then continuing into phases 3–5 and reporting
while v1 terminates the copilot run. v1's `continue_on_module_failure=true`
option is an INTENTIONAL DIVERGENCE, not parity: it runs wave 2 after a
wave-1 failure, which the parent never does (the parent skips wave 2
unconditionally on wave-1 failure and only continues the LATER phases);
the option's v1 behavior is pinned by
`test_continue_on_module_failure_parity_mode` — the test name predates
this correction and pins v1 only. Rollback value =
the parent's phase code paths, which is what live incidents would
implicate.

Three contract deviations, each with an explicit resolution:
(1) **env mutation** — v1 mutates `os.environ` via `_export_all_settings`;
the "process env never mutated" guardrail becomes
global-except-`rebase_native.py` at PR4d (a scoped exemption list containing
exactly that module) and fully global at PR7, when the bridge itself is
deleted per §2.9. Owner-accepted exemption with a sunset.
(2) **push choke point — a RECORDED TEMPORARY NORMATIVE EXCEPTION to SPEC
C4, owner-signed, sunset PR7.** Wrapping each of the parent's internal
pushes (phase 4 pushes repeatedly across CI-debug iterations; branch
creation uses raw `--force`) would modify the implementation v1 exists to
preserve, so C4 is formally excepted for v1 — narrowly, with these PR4c
mitigations, each pinned by test: (a) `push.guard_push` runs as
AUTHORIZATION at v1's phase-4 entry — a `PushPolicy` for the rebase branch;
deny ⇒ FORBIDDEN before any parent code runs; the authorization covers that
phase's pushes to that branch (it is NOT per-push interception — stated
openly as the exception's content); (b) branch equality holds by
construction: v1 passes `REBASE_BRANCH` to the parent from the same
manifest field (`repo.rebase_branch`) the `PushPolicy` was built from;
(c) `REMOTE_ENABLED` is forced off at v1 entry, making the hybrid
`remote_sync` force-push paths unreachable; (d) protected branches can
never be pushed: `guard_push` denies them at authorization and the parent
only ever pushes `REBASE_BRANCH`. The §5.2 push WAL governs the **v3
pipeline only**; v1's pushes have no WAL — part of this exception,
dying with it at PR7.
(3) **mode contract (Rev 8 §2.1)** — v1's phase handlers ignore
`TaskSpec.report_only`, so a defaulted mode could reach mutating phases.
**PR4c obligation:** v1 registers with a mode REJECTION — it accepts only
explicit `rebase_mode=full` and returns BLOCKED for every other mode
(pinned by test). The rollback path is a full run by definition; v1 never
implements the mode matrix.

## 5. Delivery sequence and status

| PR | Scope | Status |
|---|---|---|
| PR0 | Executor lifecycle (behavior-preserving) | **DONE — GPT APPROVED** (4 rounds) |
| PR1 | Testing substrate + watchdog data | **DONE — GPT APPROVED** (9 finding rounds + agreement round accepting 2 owner positions + verification round) |
| PR2 | Phase-1 cluster: wheel, guard, assign, path_sync, api-drift guard | **DONE — GPT APPROVED** (5 finding rounds + 2 verification rounds; see §5.1) |
| PR3 | Push cluster (contracts: §5.2): `gitio.py`, `push_to_ci.py` preflights, `PushPolicy.lease_expect`/`create_only`, push WAL + exact reconciliation | **DONE — GPT APPROVED** (5 finding rounds + 1 verification; 23 findings, all fixed with regression tests; see §6 items 12–14 for the recorded divergences) |
| PR4a | Engine core, unwired: agent loop, ToolDefs + opt-in dispatch scoping, substate, loop-scoped `RuntimeRegistry`, planner `requires` filter + `missing_capabilities()` for exact-repo playbooks | **DONE — GPT APPROVED** (5 finding rounds, 15 findings all fixed; see §6 items 15–17) |
| PR4b | Adapter knowledge: templates + prompt/request-shape goldens, prompt_data (builder flavor; DRIFT_TRIAGE #1), hooks base + adapter hooks (HIGH-RISK `rebase` section), `imx-omni-pytest`, `module_rebase.py` + `phase1_steps.py` | **DONE — GPT APPROVED** (4 finding rounds, 9 findings all fixed; see §6 items 18–21) |
| PR4c | Assembly: test/ci loops, v3 step set incl. `push_gate`, `resolve_effective_mode` + governance write-back (Rev 8 §2.1), transition-table wiring (Rev 8 §3.1), agent-shell scrub + model-download notification hook wiring, **manifest push-section update** (§5.3), v1 re-registered as `repo-rebase-native-v1` **with its four §4 obligations: guard_push authorization at phase-4 entry, explicit-`full`-only mode rejection, `locks/omni.lock` shared-lock participation, `REMOTE_ENABLED` forced off** | **DONE — GPT APPROVED** (5 finding rounds + 2 verification rounds; 51 findings all fixed with dedicated regression tests; final verdict "No findings" at cd93dcb; see §6 items 22–28) |
| PR5 | Parity completion: tier-1 goldens, `shell_golden.json`, `DRIFT_TRIAGE.md` resolution, report-only dry path, timed rollback rehearsal | planned |
| EXT1 | External checkout: startup flock guard, pinned SHA | planned |
| PR6 | Cutover (GPU box + human): §8 validation, playbook flip, `.env` arming | planned |
| PR4d | Knowledge migration + runtime-dir cutover (post-validation; env-bridge deletion moved to PR7 per §2.9) | planned |
| PR7 | Retirement: delete external delegation, archive parent repo | planned |

### 5.1 PR2 review outcome

Five finding rounds (6+5+4+4+3 = **22 findings**, every one fixed with a
dedicated regression test in the same round) + two verification rounds: the
first confirmed one fix and found **2 residual gaps**, both fixed (`9f84e36` —
notably `_terminate_tree` stopped expanding descendants entirely, closing a
legacy-root laundering path by construction); the second returned **APPROVE
with "No findings"**. Full review transcripts are archived per round.

### 5.2 PR3 normative core (Rev 8 §3.2, extended)

Before any `git push`, persist durably (tmp+fsync+replace) a record carrying
the full **push identity**, not just OIDs:
`{repo_root, remote_name, remote_url_credential_free, dest_ref
(refs/heads/<branch>), remote_pre_push_oid | ABSENT, intended_oid,
state: intent}`; after acceptance mark `state: pushed`. Crash between ⇒
re-entry first verifies the remote identity (credential-free URL of
`remote_name` still matches the record — a reconfigured remote ⇒ ESCALATE,
never compare OIDs against a different repository), then reconciles by
reading the remote ref: remote == intended ⇒ mark pushed; remote == pre-push
⇒ retry; anything else ⇒ ESCALATE (never guess). URL resolution (SSH→HTTPS
token form) records the credential-free canonical form. Rollback =
reverse-order over the log; `ABSENT` branches roll back by lease-protected
deletion. Retries: bounded, exponential from `PUSH_RETRY_BASE_DELAY_SEC`,
immediate abort on auth/permission errors (parent parity). Crash tests per
surface.

### 5.3 Push authorization resolution

Today `PushPolicy.allowed` defaults false and the adapter manifest declares
`push.allowed: false` ("deliver via PR; never direct-push main") — correct
for every current playbook, and the rebase pipeline would be unable to push.
Resolution (lands in PR4c as a human-gated HIGH_RISK manifest edit): the push
section gains `rebase_branch_allowed: true` scoped to `repo.rebase_branch`
(`dev/vllm-align`) only; the v3 pipeline constructs its `PushPolicy` for
exactly that branch; `main` stays protected regardless. Unchanged double
gate: `push.guard_push` remains the single choke point and `ALLOW_PUSH=1` is
still required at execution time (dry-run otherwise).

## 6. Deltas vs Rev 8 (as-built decisions, each reviewer-driven)

1. **Guard split instead of guard extension.** Rev 8 said "extend
   `workspace.guard_clean`". The mutating passes (stale merge/cherry-pick/
   revert/rebase abort; pattern-driven untracked-artifact discard) violate the
   enforced `StepSpec.risk` contract on a `read` step, so they live in a new
   `workspace.guard_clean_rebase` step with `risk: write_workspace`;
   `guard_clean` stays byte-identical for every existing playbook.
2. **Snapshot identity machinery.** Rev 8 only required "attempt-scoped
   diffs / tree kills". Five review rounds hardened this into the
   identity-bound accumulate-only snapshot described in §4 — a family of
   pid-reuse/laundering races the shell parent simply had.
3. **`local_paths` union seeding pulled into PR2.** Rev 8 deferred the module
   map refresh to PR4b. The manifest's `local_paths` are now the UNION of the
   original coarse prefixes and every parent `MODULE_OMNI_FILES` entry not
   covered by them (additive: prefix-matching consumers only gain coverage);
   the full audited refresh remains PR4b.
4. **Curated path-sync merges, never replaces.** The parent's sync replaced
   list values; ours merges curated coverage into surviving entries because
   the manifest is a union by design (coarse prefixes must survive).
5. **Repo-scoped install-lock release.** The parent pkill'd every
   `uv pip install` on the host (single-tenant box); the port kills only
   processes whose `/proc/<pid>/cwd` resolves inside the target repo.
6. **api_drift_guard divergences (2, documented in the file):** the pooling
   constructor entry names `ServingPooling` (the parent's
   `OpenAIServingPooling` could never import, leaving that check silently
   dead), and constructor-check import failures now count as mismatches
   instead of silent SKIPs. `INHERITANCE_MAP` keeps SKIP semantics.
7. **Literal git pathspecs + transactional decisions.** Every decision-driven
   git operation uses `:(literal)` pathspecs; the whole dirty-worktree
   decision (all repos, all shapes, discard∩commit=∅) validates before any
   irreversible mutation.
8. **Explicit hardware-skip outcomes.** The runner returns a typed
   `skipped` outcome (with reason) when a job's GPU requirement is not met —
   the parent's silent rc=0 pass could not be told apart from success.
   Deliberate improvement, pinned by test.
9. **`nvidia-smi pmon` PID column corrected.** The parent awk'd field 1 (the
   GPU index) — on GPU 0 that meant `kill 0`, signalling its own process
   group. The port reads field 2 and rejects non-positive pids. Deliberately
   fixed, not ported.
10. **Not yet ported, scheduled (owner-visible deferrals):** the
   model-download email notification the parent fires before test attempts
   (`test_runner.sh` → `send_model_download_email.py`) — wired via the
   runner's notification hooks in PR4c; `run_module_pytest.sh`'s replacement
   command `imx-omni-pytest` — PR4b (nothing references it earlier);
   **parity tiers 2–4, `shell_golden.json`, and `DRIFT_TRIAGE.md`** — Rev 8
   scoped these to PR1, but PR1 as built shipped behavior-level pins only;
   the recorded-fixture replay tiers and the one-time GPU-box `declare -p`
   capture move to **PR5** with the tier-1 goldens (sequencing delta: the
   drift-triage decision still gates cutover, unchanged).
11a. **PR4a hardening beyond the parent (recorded):** the plan gate
   unlocks only on a SUCCESSFUL decision write, rejects gated calls at
   dispatch (advertisement is not enforcement), and confines pre-decision
   `write_file` to the plan directory under canonical resolved-path
   containment (traversal/sibling/symlink-loop spellings lock).
15. **Truncated text-only responses are not completions (PR4a).** The parent
   reported done=True when a max_tokens-cut response carried no tool calls —
   the port returns done=False (a half-finished module must not read as
   success).
16. **Paginated reads label physical lines (PR4a).** The parent labeled the
   first returned line as `offset` while skipping `offset` lines; the port
   labels offset+1 correctly.
17. **The loop enforces the shared served-model guard (PR4a).** The parent
   never checked `response.model`; the port aborts (or warns, per
   MODEL_MISMATCH_POLICY) via the shared canonical_model normalization.
18. **Live prompts use the shipped stack (PR4b).** The parity templates and
   maps stay parent-verbatim for the goldens; LIVE renders use a template
   variant whose only delta is the wrapper prose (pinned to two lines),
   reference `imx-omni-pytest`, and fix the parent's import-check quoting
   bug (single-quoted payload containing quotes → NameError).
19. **The plan gate persists across debug retries (PR4b).** The parent
   re-locked every debug retry while its debug prompt carried no plan
   contract — debug agents could never edit. The port carries `plan_done`
   across attempts.
20. **Tier-2 watchdog decisions are RECORDED under the no-LLM reviewer
   (PR4b).** An explicit CONTINUE reviewer replaces the silent
   short-circuit so the learning pipeline (noise promotion from accumulated
   CONTINUEs) is fed; the eco-tier LLM reviewer swaps in at PR4c.
21. **GPU mutex ≠ hardware gate (PR4b).** `imx-omni-pytest` serializes on
   the lock with `min_gpus=0` — a GPU-less box RUNS the command instead of
   skip-rc=0 false-passing.
11. **Known accepted micro-divergence:** pin regexes use `[ \t]` where the
   shell's `[[:space:]]` also matched `\r` — unobservable on LF-normalized
   repos; goes to `DRIFT_TRIAGE.md` in PR5 rather than silently widening.
12. **Branch creation is create-only (PR3).** The parent used raw `--force`
   when the remote branch did not exist; the port pushes under an
   ABSENCE-pinned lease (`--force-with-lease=<branch>:`) — creation cannot
   silently fast-forward a branch a racer made, and C4's with-lease-only
   rule holds. An exact-commit racer is a git no-op and harmless.
13. **Generated-output unstaging fails closed (PR3).** The parent tolerated
   per-path reset failures (`|| true`); the port raises — a still-staged
   generated file would otherwise be committed in violation of the
   never-committed promise.
14. **Push transport hygiene beyond the parent (PR3).** Push URLs resolve
   via `get-url --push` (fork pushurl honored); tokens and configured
   userinfo never reach argv/log/error text (header-only auth,
   case-insensitive stripping); the push WAL stores transport-independent
   canonical repository identities.
22. **Mode governance is opt-in per playbook (PR4c).** `Playbook.mode_aware`
   gates `resolve_effective_mode` in `run_task`/`run_playbook`; the LOCKED
   `repo-rebase` does not declare it, so its specs are untouched —
   byte-identical behavior (the §2.1 "for repo_rebase" scope refined to
   "for mode-aware playbooks", pinned by
   `test_locked_playbook_is_not_mode_governed`).
23. **Composite `mode_runs_*` state flags (PR4c).** The executor's `when:`
   is single-key, so the §2.2 or-of-modes matrix is precomputed in
   `mode_state_flags` (`mode_runs_local_tests`, `mode_runs_push_gate`,
   `mode_runs_remote_ci`) — one authority, matrix pinned against the real
   yaml gates per mode.
24. **Terminal rows realized at step level (PR4c).** Rev 8 §3.1's
   orchestration finalizer is approximated by `rebase.v3_finalize` running
   AFTER `report.final_summary` (row 2: RUN_REPORT exists, then
   BLOCKED/exit-3 with substate `phase=needs_human`), plus a
   prelude-registered lifecycle finalizer that writes a terminal
   RUN_REPORT.md when a run blocks before the report step (row 3
   artifacts; augments, never upgrades, never overwrites).
25. **Structural-failure taxonomy depth (PR4c).** Beyond §2.3's list, the
   port classifies as STRUCTURAL: agent-loop `done=False` (always
   machinery — auth/stream/mismatch/truncation/turn budget; a finishing
   agent returns done=True), debug-machinery failures (missing backend,
   crash, unverifiable re-run), baseline infra outcomes
   (regression-preserving, never "pre-existing"), zero runnable local jobs
   (`manifest_empty`), CI jobs without a per-job terminal state
   (`incomplete`, missing exit_status ≠ 0), and build-op recovery is
   intent-only with single-use op-id identity.
26. **Debug rollback handles staged new files (PR4c — fix over the
   parent).** The parent's bulk `git checkout <snap> -- <paths>` silently
   failed once a debug attempt created-and-staged a file, leaving every
   tracked edit in place; the port splits snapshot-known (restore) from
   attempt-created (unstage + delete) via `cat-file -e`.
27. **Live-tree adaptations (PR4c).** `yaml_dir: .buildkite/cuda` — the
   live tree nests pipelines per accelerator and the parent's hardcoded
   `.buildkite` finds zero jobs today (DRIFT_TRIAGE #5); pipeline-level
   `env:` mappings reach every job (job exports win); both clean-tree
   guards accept `ignore_untracked_prefixes` so the persistent shared
   flock under `locks/` (which survives release BY DESIGN) never reads as
   dirt and is never discarded while held.
28. **Model-download notification transport (PR4c).** Detection is
   parent-verbatim (same-line `hf download` regex, HF-cache snapshot
   probe, durable once-per-job marker with the parent's filename), but
   the transport is a `model_download_expected` trace event surfaced in
   the run report instead of the parent's SMTP mailer — copilot-native
   observability, no email credentials in the engine.

## 7. Testing state

- Full offline suite: **646 tests green (+1 skip)**, no GPU/network/API key.
- New pinned families: run-lifecycle (14), testing substrate (~75, incl.
  identity/laundering races each with a dedicated regression test), phase-1
  cluster (~40 incl. `test_phase1_partial_e2e` chaining guard → wheel pick →
  pin → assignment → path-sync over fixture git repos), push cluster (31
  incl. a real-bare-remote partial e2e with crash/resume/supersession
  reconciliation and a raced create-only push), assembly (~40: mode truth
  table cell-by-cell + per-mode matrix against the real yaml gates,
  push-gate taxonomy incl. logged overrides, manifest build over nested
  fixtures, test/CI loop decision matrices, production backends with
  populated stores, report-only partial e2e with a pre-existing lock file,
  resume lock reacquisition, debug snapshot/restore, scratch lifecycle).
- Repo-neutrality: leak-scan ceilings unchanged; `rebase_engine/` is clean.
- Parity: behavior-level parity pinned per module (walk order, double-probed
  baseline fallback, sed-equivalent pin edits, decision JSON schema);
  byte-level goldens (prompts, request payloads, shell command echo) land in
  PR4b/PR5 per Rev 8.

## 8. Validation, staged enablement, rollback

Controlled comparison (frozen SHAs, restored knowledge snapshots, isolated
clones, separate validation branches); one external baseline run + one
supervised v3 full validation run; gate = deterministic harness green + live
outcome equivalence + 25% wall-clock bound + human-signed COMPARISON.md.

**Supervised-run count, unambiguous:** stage 3 (unsupervised push-capable
`full`) requires **2 supervised clean full runs total, of which the PR6
validation run counts as the first**; one additional supervised full run
happens during soak. Staged soak: 3 clean `report_only` nightlies (semantic
diffs vs frozen baseline) → 2 clean `local_ci` runs → the second supervised
full run → unsupervised full.

**PR4d re-validation gate (new — closes a Rev 8 gap):** PR4d (knowledge
migration, runtime-dir cutover) changes the runtime
configuration PR6 validated — including stores the phase-2 agents and
curation read/write. After PR4d lands, the soak clock partially resets and
must cover PR4d's actual blast radius: 1 clean `report_only` run with
semantic diffs against pre-PR4d baseline outputs, 1 supervised `local_ci`
run, **and the soak's second supervised FULL run is deliberately scheduled
post-PR4d** (exercising phase-2 agents, knowledge writes/curation, and push
behavior on the final runtime configuration — this run satisfies both the
stage-3 requirement and the PR4d gate). **PR4d rollback is layered:** the
knowledge/runtime-dir side rolls back via the versioned backup
(non-destructive move) plus a config flag keeping the old runtime dir
selectable for one full soak period; the code side (store cutover wiring)
is a single revertible commit — rollback = `git
revert` of that commit + backup restore, rehearsed as part of PR4d
acceptance. PR7 does not start until the post-PR4d soak requirement is met.

**Rollback:** pre-PR7, the `repo-rebase-native-v1` backend (imports the
external `agent` package in-process) or a fresh external run. **Post-PR7 the
v1 backend is dead by construction** — PR7 deletes the delegation code
(`rebase.run_external`, monitor helpers, v1 playbook, orchestrator settings)
as well as retiring the external repo. PR7's RUNBOOK restore procedure
therefore restores BOTH sides: (1) **code**: PR7 tags the copilot at
`pre-pr7-retirement` immediately before the deletion commit; restore =
deploy the copilot at that tag (or revert the PR7 commit), which brings back
the delegating playbook, its registered steps, and v1; (2) **external**: the
parent repo is archived as a tagged clone PLUS a mutable-state snapshot — a
tag alone cannot carry gitignored, dirty, or untracked runtime state. The
archival step runs **while holding the checkout lock that ALL users of the
checkout share** — EXT1 makes the external executable acquire
`locks/omni.lock` at startup, and PR4c makes the in-process v1 backend
acquire the SAME flock at run start (shared-lock participation, pinned by
test), so holding it during archival proves no external and no v1 run is
active. The step then: (a) commits all dirty/untracked runtime state
onto a dedicated archival branch before tagging — this covers
`agent/skills/` (usage updates rewrite `SKILL.md`; `_candidates.json` is
generated) and anything else the working tree accumulated, with a
clean-tree check proving nothing was missed; (b) captures a
SQLite-consistent copy of the gitignored debug DB (`sqlite3 .backup`) and a
tarball of `rebase_logs/`, stored alongside the archive. **Secrets are
never archived**: the parent reads its env from `agent/.env` (preferred)
with a root-`.env` fallback — and the canonical checkout currently uses the
root `.env` — so archival inventories key NAMES from whichever parent env
source(s) actually exist at archive time, values omitted; restore recreates
the same file(s) at the same path(s) with values from the owner's secret
store. Restore = re-clone the archive tag to the canonical path, unpack the
state snapshot, recreate the parent env file(s) from the inventory, and
re-add the copilot `.env` orchestrator block from its timestamped backup. (By PR7 the canonical
knowledge already lives in the copilot runtime stores via PR4d's migration —
the snapshot is belt-and-braces for parent-side residue.) The combined
restore is rehearsed once, timed, as part of PR7 acceptance. Cutover rollback itself is rehearsed
(<30 min) before PR6; abort criteria recorded in the RUNBOOK.

## 9. Top open risks

1. Dual command source false-pass (shell §10 slug → empty command → rc=0) —
   surfaced by shell-golden into `DRIFT_TRIAGE.md` (PR5), decided pre-cutover.
2. Push crash windows — PR3's write-ahead log + exact reconciliation.
3. Agent-mutation runs — risk reduction only (scrub, scratch clones, pushurl
   friction); the control is the Decision-5 recorded risk acceptance; OS
   sandboxing stays future hardening.
4. Validation sample size — deterministic harness is primary evidence; ≥7
   live data points before retirement.
