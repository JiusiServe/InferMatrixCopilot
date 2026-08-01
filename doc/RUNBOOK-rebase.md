# RUNBOOK — repo-rebase v3 cutover operations

The operational companion to `doc/PLAN-rebase-merge.md` (§3.3 rollback,
§8 validation/staged enablement). Everything here is human-executed; the
plan doc holds the contracts, this holds the switches and checklists.

## EXT1 — external checkout pin (DONE, 2026-08-01)

- **Canonical external checkout:**
  `/data/zhoutaichang/rebase/vllm-omni-rebase-agent`
- **Pinned SHA:** `71222e8913558740857f9f981e8ed97b21f2c44f`
  (`fix(ext1): lock file invisible to workspace hygiene`, on top of
  `015344d feat(ext1): startup checkout flock`) — these two commits ARE
  the whole EXT1 change (guard module + orchestrator hook +
  info/exclude hygiene shield), independently revertible with
  `git revert 71222e8 015344d`.
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
3. **Target venv configured:** `VLLM_OMNI_VENV` (manifest `repo.venv`)
   must point at the vllm-omni dev venv; wheel installs and the local
   test loop BLOCK without it.
4. **DRIFT_TRIAGE has no undecided entries** (currently: all decided —
   #1 flavors frozen, #4 manifest-built slug set, #6 map flavors, #7
   declared-vs-computed mapping).
5. **Validation branches** `rebase-val-ext-<date>` / `rebase-val-nat-<date>`
   created; knowledge snapshots taken (`backups/<ts>/`).
6. **Supervised v3 full run** (`ALLOW_PUSH=1`, human attached) per plan
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
| EXT1 | `git revert 71222e8 015344d` in the canonical checkout |

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
