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

### NEW findings needing owner decisions before the supervised run

- **A. Checkout split**: the deployed parent operates on
  `/data/zhoutaichang/rebase/vllm-omni` (dev/vllm-align) while the
  copilot adapter points at `/data/zhoutaichang/copilot/vllm-omni`
  (main). EXT1 exclusion is per-checkout (correct semantics), but the
  §8 comparison needs ONE target world — recommend pointing
  `VLLM_OMNI_REPO` at the deployed checkout (or isolated clones per §8)
  for the validation run.
- **B. GPU window**: schedule the supervised run OUTSIDE ~16:00–18:00
  UTC — the nightly perf CI seizes all GPUs and KILLS GPU compute
  processes after a 1-hour wait; a mid-flight validation would be shot.
- **C. Buildkite schedule race**: the pipeline's own daily Align
  schedule builds `dev/vllm-align`; recommend PAUSING the two schedules
  for the validation window (op-recorded-only cancellation protects us,
  but a scheduled build would pollute the outcome comparison).
