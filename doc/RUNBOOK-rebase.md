# RUNBOOK — repo-rebase v3 cutover operations

The operational companion to `doc/PLAN-rebase-merge.md` (§3.3 rollback,
§8 validation/staged enablement). Everything here is human-executed; the
plan doc holds the contracts, this holds the switches and checklists.

## EXT1 — external checkout pin (DONE, 2026-08-01)

- **Canonical external checkout:**
  `/data/zhoutaichang/rebase/vllm-omni-rebase-agent`
- **Pinned SHA:** `0395bbe` (EXT1 = six commits `0395bbe 353b0a6
  8ffcc6c 634b002 71222e8 015344d`: guard module + orchestrator hook
  + fail-closed root-anchored symlink-hostile atomic hygiene shield +
  baseline-under-lock ordering + errno-precise diagnostics +
  validated gitdir + no checkout fabrication), independently
  revertible with `git revert 0395bbe 353b0a6 8ffcc6c 634b002
  71222e8 015344d`.
- **Startup guard:** the orchestrator flocks
  `<omni_checkout>/locks/omni.lock` after the dry-run exit and before
  resume detection; refuses (exit 3) when a copilot run holds it.
  Mutual exclusion is pinned both directions by the copilot's
  `test/test_ext1_checkout_guard.py`.
- **Working-tree note at pin time:** the deployed checkout carries
  UNCOMMITTED owner changes (config.sh/§10 maps, config.py,
  debug_memory_store.py, test_watchdog.sh, skills, task scripts,
  nightly_rebase_cron.sh, …). The PR5 `shell_golden.json` was captured
  from this WORKING TREE (the deployed truth), so the golden describes
  the live behavior, not the pinned commit's. Any comparison run from a
  fresh clone of the pinned SHA will differ from the deployed instance —
  baseline runs for §8 must use the deployed working tree as-is.

## CI-W — v3_ci remote-CI wiring (DONE, 2026-08-01)

The PR4c stub is gone: `rebase.v3_ci` is live-wired (plan §5 CI-W row,
§6.30 divergences; GPT "No findings" at 5bf7100). Operational notes:

- **remote_ci and full modes now reach a REAL provider.** The step needs
  `BUILDKITE_API_TOKEN`, the adapter's `ci.org` + `rebase.ci.pipeline`
  (build-under-test `vllm-omni-release`) + `rebase.ci.baseline_pipeline`
  (`vllm-omni-rebase`), and pushes ONLY the adapter-declared
  `push.rebase_branch` (`dev/vllm-align`) as `push.signoff`
  (tzhouam <tzhouam@connect.ust.hk>). `ALLOW_PUSH=1` still gates
  execution (dry-run is FORBIDDEN at phase 4, per the §2.2 matrix).
- **Knobs** (`.env`, neutral): `REBASE_CI_RETRIES=2`,
  `REBASE_CI_JOB_RETRY_MAX=2`, `REBASE_CI_POLL_SEC=120`,
  `REBASE_CI_TIMEOUT_SEC=10800`, `REBASE_CI_SETTLE_SEC=60`.
- **Ownership safety (supervised-run relevant):** the run refuses to
  push/create while any UNOWNED build is active on the rebase branch —
  pause the Buildkite Align schedules during validation (owner decision
  C) or expect `refused` terminals. Owned = this run's op-recorded
  builds + webhook artifacts of its own pushes; schedule/api builds at
  the same commit are adopted monitor-only.
- **Abort cleanup:** a cancelled/killed run cancels its own op-recorded
  active builds via the lifecycle finalizer; adopted builds are never
  touched. Rollback inventory row "running CI → cancel op-recorded
  builds" is now automatic on abort; manual cancellation stays available
  through the ledger (`<run_dir>/ci_ops/*.json`) + Buildkite UI.
- **Push WAL** lives at `<run_dir>/push_wal/` (reverse-order rollback per
  the inventory below); build ops at `<run_dir>/ci_ops/`; CI job logs at
  `<run_dir>/ci_logs/`.

## PR6 preconditions (gate — none may be skipped)

1. **Timed rollback rehearsal** (< 30 min from decision to a running v1
   backend), NOT yet done — needs the owner attached:
   `./infermatrix-copilot --playbook repo-rebase-native-v1 --yes
   --task-param rebase_mode=full` from a clean state; stopwatch from the
   "roll back" decision to the v1 prelude completing. Record the time
   here.
2. **Tier/backend config fix on this host:** the eco endpoint
   (api.deepseek.com) SUBSTITUTES model names (served `deepseek-v4-flash`
   for a requested Claude model). The copilot's served-model guard
   correctly refuses; live agent runs need either a truthful backend or
   an explicit, recorded `MODEL_MISMATCH_POLICY=warn` decision. Do not
   run the supervised validation with a silently-substituting backend.
3. **v1 rollback path points at the CANONICAL checkout:** a STALE
   sibling working copy exists at `copilot/vllm-omni-rebase-agent`
   (no EXT1) and `Settings.rebase_agent_root` DEFAULTS to it — set
   `REBASE_AGENT_ROOT=/data/zhoutaichang/rebase/vllm-omni-rebase-agent`
   in `.env` so v1 backend runs import the EXT1-guarded code (or
   delete/refresh the stale copy).
4. **Target venv configured:** `VLLM_OMNI_VENV` (manifest `repo.venv`)
   must point at the vllm-omni dev venv; wheel installs and the local
   test loop BLOCK without it.
5. **DRIFT_TRIAGE has no undecided entries** (currently: all decided —
   #1 flavors frozen, #4 manifest-built slug set, #6 map flavors, #7
   declared-vs-computed mapping).
6. **Validation branches** `rebase-val-ext-<date>` / `rebase-val-nat-<date>`
   created; knowledge snapshots taken (`backups/<ts>/`).
7. **Supervised v3 full run** (`ALLOW_PUSH=1`, human attached) per plan
   §8; comparison over the MANIFEST-BUILT slug set (DRIFT #4), module
   outcomes mapped through the golden's `assignment_routing` (DRIFT #7).

## Rollback inventory (reverse order of application)

| Surface | Rollback |
|---|---|
| Playbook flip (v3 → locked) | revert the PR6 promotion commit |
| `.env` armed block | restore the timestamped backup made at arming |
| Running CI builds | cancel op-recorded builds only (`ops/` records; never a build the run cannot prove it created) |
| Pushed refs | reverse-order over the push WAL; `ABSENT`-recorded branches roll back by lease-protected deletion |
| Validation branches | deleted after the comparison freeze |
| Mutated omni checkout | snapshot restore (attempt-scoped) or manual steps from the run's DIAGNOSTICS |
| Upstream | per-run scratch clone — discarded automatically by the run finalizer |
| Runtime knowledge | move `backups/<ts>/` back (non-destructive) |
| EXT1 | `git revert 0395bbe 353b0a6 8ffcc6c 634b002 71222e8 015344d` in the canonical checkout |

**Abort criteria** (any one triggers rollback + investigation): §8
validation gate fails; > 25 % end-to-end wall-clock regression; any
unowned CI mutation observed; a lock leak (post-run lock-dir scan); any
ESCALATION during soak stages 1–2.

## Staged enablement thresholds (plan §8)

1. `report_only` nightly, unsupervised → promote after **3 consecutive
   clean runs** (exit 0, no lock leaks, no ESCALATION.md) with the
   deterministic outputs (manifest, drift scan, assignment preview)
   diffed clean against the frozen baseline — the seed baseline is the
   2026-08-01 dry run (54 jobs / 310 changes).
2. `local_ci`, unsupervised (covered by the recorded Decision-1 risk
   acceptance) → promote after **2 consecutive runs** with zero new
   DRIFT/parity items.
3. Push-capable `full`, unsupervised → after **2 supervised clean full
   runs** (the PR6 validation run counts as the first; the second is
   deliberately scheduled post-PR4d).

## PR6 preflight — evidence & status (2026-08-01, session-executed)

### No-live-consumer evidence (plan §1 re-verification: CONFIRMED)

1. **Scheduler scan**: root's crontab has exactly ONE entry — `0 16 * * *
   /rebase/nightly_local.sh` — a nightly ACCURACY/PERF CI over a third
   checkout (`/rebase/vllm-omni`), NOT the rebase orchestrator. Nothing
   schedules the orchestrator: `nightly_rebase_cron.sh` (designed for
   18:30 UTC) is present but NOT installed in any crontab/timer. No
   orchestrator process is running; the parent's `state.json` is the
   known Jul-25 mid-flight recording (`phase=local_testing`).
2. **Buildkite, 30 days** (`vllm/vllm-omni-rebase`, read-only API query):
   100 builds, ALL attributed — the pipeline's OWN daily schedules
   ("Scheduled build" on `main`, "Scheduled nightly build - Align" on
   `dev/vllm-align`), the owner's manual API builds (Jul 27–28 v0.26.0
   session), and webhook builds. ZERO unattributed; zero
   `imx_op_id`-stamped builds (expected — the copilot has never pushed).

### Preconditions resolved this session

- **#2 tier config**: `AGENT_MODEL="claude-sonnet-5"` was untruthful on
  `api.deepseek.com` (silently served `deepseek-v4-flash`; the guard
  refused). Fixed to `deepseek-v4-pro[1m]`; `doctor --probe` now verifies
  the eco tier round-trips truthfully. `.env` backup:
  `.env.backup-20260801-155809`.
- **#3 v1 rollback path**: `REBASE_AGENT_ROOT` already points at the
  canonical checkout in `.env` — satisfied.
- **#4 target venv**: `VLLM_OMNI_VENV=/data/zhoutaichang/rebase/.venv`
  added (the parent's `REBASE_VENV`).
- **Doctor**: fully green (deps/env/gh/repos/backends/playbooks/moa/probe).
- **Lock-leak scan**: both vllm-omni checkouts' `locks/omni.lock` FREE.
- **Mechanical rollback rehearsal (timed): 5 s** from decision to
  (v1 playbook resolved via `--plan-only`) + (external orchestrator
  `--dry-run` exit 0). The FULL rehearsal — to a v1 backend actually
  executing phases — remains the owner-attached gate item.

### Frozen-SHA candidates for the §8 comparison

| World | SHA | Branch |
|---|---|---|
| deployed target `rebase/vllm-omni` | `05d0926e` | dev/vllm-align |
| copilot target `copilot/vllm-omni` | `a61d5c0f` | main |
| upstream `rebase/vllm` | `ffd46bfab2` | (detached — parent wheel pin) |
| external agent | `0395bbe` | main (= EXT1 pin) |

### Owner decisions before the supervised run

- **A. Checkout split — DECIDED (owner, 2026-08-01, per
  recommendation)**: the validation target world is the DEPLOYED
  checkout `/data/zhoutaichang/rebase/vllm-omni` (dev/vllm-align) for
  BOTH the external baseline run and the v3 run. The run-day script
  below repoints `VLLM_OMNI_REPO` + `REPO_PATHS` at it for the
  validation window (timestamped `.env` backup first) and restores
  after the freeze. EXT1's per-checkout flock now covers both runs on
  the same world — which is exactly the mutual exclusion it was built
  for.
- **B. GPU window — OPEN**: schedule the supervised run OUTSIDE
  ~16:00–18:00 UTC — the nightly perf CI (`0 16 * * *` root crontab)
  seizes all GPUs and KILLS GPU compute processes after a 1-hour wait; a
  mid-flight validation would be shot. Pick the window and the
  `CUDA_VISIBLE_DEVICES` set on run day (the cron session used `4,5`).
- **C. Buildkite schedule race — OPEN (pause strongly recommended)**:
  the pipeline's own daily Align schedule builds `dev/vllm-align`;
  PAUSE the two schedules ("Scheduled build" on main, "Scheduled
  nightly build - Align") for the validation window. This is now
  doubly required: CI-W's ownership rules REFUSE to push while an
  unowned build is active on the branch, so an unpaused schedule can
  turn the v3 run into a `refused` terminal, not just pollute the
  comparison.

## Run day — PR6 validation script (owner-attached)

Sequential, copy-paste blocks; every mutation has its rollback in the
inventory above. Stop at any ✗ — do not improvise past a failed check.
Shorthands used throughout:

```bash
export COP=/data/zhoutaichang/copilot/InferMatrixCopilot
export AG=/data/zhoutaichang/rebase/vllm-omni-rebase-agent      # EXT1 pin
export TGT=/data/zhoutaichang/rebase/vllm-omni                  # decision A
export UPSTREAM_SHA=ffd46bfab2128bb84146050e98b51a617c6575ab    # frozen vllm
export VAL=$(date -u +%Y%m%d)                                   # branch suffix
```

### Phase 0 — preflight (T-1 day is fine; ~15 min)

- [ ] Decisions **B** (window + GPU set) and **C** (schedules paused in
      the Buildkite UI) are settled; record them here.
- [ ] `cd $COP && git status --short` → clean; `git log --oneline -1`
      recorded as the copilot SHA under test.
- [ ] `git -C $AG log --oneline -1` → still `0395bbe`+working tree
      (EXT1 pin; the working tree is the deployed truth — do NOT clean
      it).
- [ ] `./infermatrix-copilot doctor --probe` → fully green (truthful
      eco round-trip; `MODEL_MISMATCH_POLICY` stays `fail`).
- [ ] Locks free: `ls $TGT/locks/ $COP/../vllm-omni/locks/ 2>/dev/null`
      → no held flocks (probe: both `omni.lock` acquirable).
- [ ] No orchestrator running: `pgrep -af omni-rebase-orchestrator` →
      empty.
- [ ] Freeze table below filled in (target HEAD moves daily — record
      run-day values):

```bash
git -C $TGT rev-parse HEAD dev/vllm-align   # target start SHA
grep -n "LAST_REBASE_VLLM_COMMIT" $AG/config.sh   # v3 last_rebase baseline
```

| Frozen world | Value (fill on run day) |
|---|---|
| target `$TGT` dev/vllm-align start SHA | ☐ |
| upstream vllm | `ffd46bfab2128bb84146050e98b51a617c6575ab` |
| external agent | `0395bbe` + deployed working tree |
| copilot | ☐ (git log -1 above) |
| `LAST_REBASE_VLLM_COMMIT` (config.sh effective) | ☐ (default `d4004455d235…`) |

### Phase 1 — snapshots, branches, .env repoint (~10 min)

```bash
TS=$(date +%Y%m%d-%H%M%S)
# knowledge snapshot (restored before EACH run; non-destructive rollback)
mkdir -p $AG/backups/$TS
cp -a $AG/agent/store/debug_memory.db $AG/agent/skills \
      $AG/rebase_logs/state.json $AG/backups/$TS/
# validation branches from the frozen start SHA (one per world)
git -C $TGT branch rebase-val-ext-$VAL dev/vllm-align
git -C $TGT branch rebase-val-nat-$VAL dev/vllm-align
# .env repoint (decision A) — timestamped backup FIRST
cd $COP && cp .env .env.backup-$TS
```

- [ ] Edit `$COP/.env`: set **every** `REPO_PATHS` line to
      `{"vllm-omni": "/data/zhoutaichang/rebase/vllm-omni"}` and
      `VLLM_OMNI_REPO="/data/zhoutaichang/rebase/vllm-omni"`
      (duplicate keys exist — last one wins, fix both). Leave
      `ALLOW_PUSH` at 0 (armed per-command in Phase 4 only).
- [ ] TEMPORARY manifest edit (HIGH-RISK section, owner-only, reverted
      in Phase 6): in `adapters/vllm_omni/manifest.yaml` set
      `push.rebase_branch: rebase-val-nat-<VAL>` so the v3 run pushes
      the VALIDATION branch, never dev/vllm-align. Do not commit.
- [ ] `./infermatrix-copilot doctor` re-run green against the deployed
      checkout.

### Phase 2 — timed FULL rollback rehearsal (gate item 1; target < 30 min)

Stopwatch starts at the words "roll back", ends when the v1 backend is
observably executing (prelude complete, phase 1 underway):

```bash
date -u +%T   # stopwatch start
cd $COP && ./infermatrix-copilot --playbook repo-rebase-native-v1 --yes \
    --task-param rebase_mode=full
# watch until the v1 prelude completes and phase-1 output appears, then
# Ctrl-C (this rehearses the SWITCH, not a full v1 run)
date -u +%T   # stopwatch stop — record below
```

- [ ] Time recorded: ☐ (must be < 30 min; the 2026-08-01 mechanical
      rehearsal was 5 s to plan-resolution + dry-run exit 0)
- [ ] Post-abort: locks free again; no stray processes
      (`pgrep -af rebase`).

### Phase 3 — external baseline run to phase=done (hours; GPU window per B)

The deployed parent, deployed working tree, validation branch, frozen
upstream. Its own flock on `$TGT/locks/omni.lock` excludes the copilot
for the duration:

```bash
git -C $TGT checkout rebase-val-ext-$VAL && git -C $TGT status --short  # clean
cd $AG && REBASE_BRANCH=rebase-val-ext-$VAL \
    FORCE_VLLM_COMMIT=$UPSTREAM_SHA \
    CUDA_VISIBLE_DEVICES=<per decision B> \
    /data/zhoutaichang/rebase/.venv/bin/omni-rebase-orchestrator \
    2>&1 | tee rebase_logs/val-ext-$VAL.log
```

- [ ] Runs to `phase=done` (`python3 -c "import json;
      print(json.load(open('$AG/rebase_logs/state.json'))['phase'])"`).
      A mid-flight failure here is a PARENT failure — investigate, do
      not paper over; the comparison needs a completed baseline.
- [ ] Archive the ext world:
      `mkdir -p $COP/validation/$VAL/ext && cp -a
      $AG/rebase_logs/state.json $AG/rebase_logs/latest
      $COP/validation/$VAL/ext/ && git -C $TGT rev-parse HEAD >
      $COP/validation/$VAL/ext/target-head`
- [ ] **Restore for the v3 run**: knowledge back to the Phase-1
      snapshot (`cp -a $AG/backups/$TS/debug_memory.db
      $AG/agent/store/; rm -rf $AG/agent/skills && cp -a
      $AG/backups/$TS/skills $AG/agent/`); target back to the frozen
      start (`git -C $TGT checkout rebase-val-nat-$VAL && git -C $TGT
      status --short` → clean); locks free; GPUs idle (`nvidia-smi`).

### Phase 4 — supervised v3 full run (human attached, ALLOW_PUSH armed per-command)

```bash
cd $COP && ALLOW_PUSH=1 CUDA_VISIBLE_DEVICES=<per decision B> \
    ./infermatrix-copilot --playbook repo-rebase-v3 --yes \
    --task-param rebase_mode=full \
    --task-param last_rebase_commit=<LAST_REBASE_VLLM_COMMIT from Phase 0> \
    --task-param force_upstream_commit=$UPSTREAM_SHA \
    2>&1 | tee validation/$VAL/nat-run.log
```

Watch for (abort → rollback inventory, in order): any push to a branch
other than `rebase-val-nat-$VAL`; any Buildkite mutation without
`imx_op_id` metadata in the trace; a `refused` terminal naming an
unowned build (check decision C's pause actually took); lock-leak or
crash. A crash is resumable (`--resume`) — the WAL/op-ledger recovery
is exactly what nine review rounds hardened.

- [ ] Terminal: exit 0 (`done`) or exit 3 with explained substate —
      record `RUN_REPORT.md`, `metrics.json`, run dir path.
- [ ] Post-run scans: locks free; `push_wal/` all `pushed`/reconciled;
      `ci_ops/` all terminal; no builds left running on Buildkite.
- [ ] Archive: `cp -a ~/.infermatrix-copilot/runs/<run-dir>
      $COP/validation/$VAL/nat`

### Phase 5 — comparison + sign-off (gate)

Per plan §8 + DRIFT #4/#7, over the MANIFEST-BUILT slug set:

- [ ] Slug sets identical (ext vs nat manifest builds).
- [ ] Per-module / per-slug outcomes equal-or-better (nat vs ext), ext
      module names mapped through the golden `assignment_routing`; one
      re-run allowed per flaky divergence, divergences investigated via
      the v1 backend — never averaged away.
- [ ] CI verdicts equal-or-better; push/commit shape identical (same
      files staged, same unstage exclusions, signed-off author).
- [ ] Wall-clock: nat ≤ 1.25 × ext end-to-end.
- [ ] `validation/$VAL/COMPARISON.md` written from the checklist above
      and **signed by the owner** (name + date in the file).

### Phase 6 — verdict

**PASS →** in one commit (the PR6 promotion): flip v3 → locked
`repo-rebase`, retire the delegating yaml, update `CLAUDE.md`'s locked-
playbook rule, revert the temporary `push.rebase_branch` edit; then arm
`.env` deliberately (new timestamped backup; `--dry-run` removal per
plan §9); unpause the Buildkite schedules; delete the validation
branches after the comparison freeze; enter staged soak stage 1
(`report_only` nightly).

**FAIL / ABORT →** rollback inventory top-to-bottom (restore
`.env.backup-$TS`, revert the manifest edit, cancel op-recorded builds,
WAL-reverse pushed refs, restore knowledge snapshot, checkout restore),
then investigate via the v1 backend. The validation branches are the
evidence — keep them until the investigation closes.
