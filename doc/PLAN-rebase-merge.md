# PLAN — Merge `vllm-omni-rebase-agent` into InferMatrixCopilot (repo-rebase v3)

Status: **active migration** on branch `feat/rebase-merge-pr0`. This document is
the as-built successor of plan Revision 8 (7 prior GPT-5.6 Sol design reviews;
owner locked all decisions 2026-07-28). It records what is now BUILT, what
changed against Rev 8 and why, and the remaining delivery sequence. Update it
at every PR boundary; it supersedes the Rev 8 file for current state.

## 1. Goal

Eliminate `repo-rebase`'s external subprocess runs by absorbing the external
5-phase LangGraph orchestrator (`vllm-omni-rebase-agent`) into the copilot,
preserving functionality and performance. Canonical external checkout:
`/data/zhoutaichang/rebase/vllm-omni-rebase-agent` (the `copilot/` clone is a
working copy). No live consumer of the external path exists (user-attested;
re-verified in the PR6 preflight).

## 2. Locked decisions (owner, 2026-07-28 — unchanged)

1. Full merge; external repo retired at the end (PR7).
2. Copilot-executor substrate; LangGraph dropped; sub-step resume preserved.
3. Full shell→Python port; remote/hybrid execution not ported
   (`capability_gap` traced where it would have been used).
4. Direct cutover after validation (§8); selectable `repo-rebase-native-v1`
   backend is the rollback, ParentStateFile dual-write dropped.
5. Offline golden-parity suite + ONE supervised real full run; staged
   enablement (report_only → local_ci → full) with recorded RUNBOOK risk
   acceptance for unsupervised agent-mutation runs.
6. Data-first knowledge: repo specifics live in `adapters/vllm_omni/`
   (manifest + data files + `hooks.py`); the engine stays repo-neutral
   (`test_repo_neutral_core` ceilings unchanged).
7. Push gate: structural failures block, test assertion failures pass through
   flagged; `strict_push_gate` available; conflicting
   `strict_push_gate`+`push_with_failures` ⇒ BLOCKED.
8. `blocked`/exit 3 reused for every needs-human terminal state.
9. Knowledge migration + env-bridge deletion (PR4d) deferred until after live
   validation.

## 3. Review & delivery protocol (owner, 2026-07-31)

Every PR must:

- **(a) reach explicit agreement with GPT-5.6 Sol** — an APPROVE verdict —
  within **max 5 finding rounds**, plus a final verification-only round
  confirming the last round's fixes (PR1 precedent). Reviews run via
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
- **Process-identity kill safety (PR1/PR2 hardening)**: every kill decision is
  identity-checked against `/proc/<pid>/stat` (starttime); descendant
  snapshots accumulate `(pid → starttime)` and never shrink; recording and
  ancestry are bound in a single stat read with a fixpoint chain anchored at
  an immutable leader identity; `kill_tree` re-validates roots after the
  descendant walk. Residual window: stat-read-to-signal gap (needs pidfds).
- **GPU serialization**: byte-compatible on-disk lock protocol with the shell
  era; flock-serialized stale-lock steal; single-tenant orphan reaping is a
  recorded owner position (reviewer-accepted).
- **Env hygiene**: allowlist-based scrub for agent shells (exact/prefix split,
  credential-suffix veto, HF token opt-in); child envs are copies — the
  copilot process env is never mutated.

## 5. Delivery sequence and status

| PR | Scope | Status |
|---|---|---|
| PR0 | Executor lifecycle (behavior-preserving) | **DONE — GPT APPROVED** (4 rounds) |
| PR1 | Testing substrate + watchdog data | **DONE — GPT APPROVED** (9 finding rounds + agreement round accepting 2 owner positions + verification round) |
| PR2 | Phase-1 cluster: wheel, guard, assign, path_sync, api-drift guard | **DONE — GPT APPROVED** (5 finding rounds + 2 verification rounds; see §5.1) |
| PR3 | Push cluster: `gitio.py` (staging/unstage of generated outputs, signed-commit retry with ruff-hook detection, clean-env push execution), `push_to_ci.py` preflights, `PushPolicy.lease_expect` (SHA-pinned force-with-lease), push write-ahead log + reconciliation | next |
| PR4a | Engine core, unwired: agent loop, ToolDefs + opt-in dispatch scoping, substate, loop-scoped `RuntimeRegistry`, planner `requires` filter | planned |
| PR4b | Adapter knowledge: hooks base + vllm-omni hooks, manifest extension (incl. audited `local_paths` refresh), prompt templates + prompt/payload goldens, `phase1_steps.py`, `module_rebase.py` | planned |
| PR4c | Assembly: test/ci loops, v3 step set incl. `push_gate`, `resolve_effective_mode` + governance write-back, transition-table wiring, v1 re-registered as `repo-rebase-native-v1` | planned |
| PR5 | Parity completion: tier-1 goldens, `shell_golden.json`, `DRIFT_TRIAGE.md` resolution, report-only dry path, timed rollback rehearsal | planned |
| EXT1 | External checkout: startup flock guard, pinned SHA | planned |
| PR6 | Cutover (GPU box + human): §8 validation, playbook flip, `.env` arming | planned |
| PR4d | Knowledge migration + env-bridge deletion (post-validation) | planned |
| PR7 | Retirement: delete external delegation, archive parent repo | planned |

### 5.1 PR2 review outcome

Five finding rounds (18 findings, every one fixed with a dedicated regression
test in the same round) + two verification rounds: the first confirmed one fix
and found residual gaps in two, both fixed (`9f84e36` — notably
`_terminate_tree` stopped expanding descendants entirely, closing a
legacy-root laundering path by construction); the second returned **APPROVE
with "No findings"**. Full review transcripts are archived per round.

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
8. **Known accepted micro-divergence:** pin regexes use `[ \t]` where the
   shell's `[[:space:]]` also matched `\r` — unobservable on LF-normalized
   repos; goes to `DRIFT_TRIAGE.md` in PR5 rather than silently widening.

## 7. Testing state

- Full offline suite: **~540 tests green**, no GPU/network/API key.
- New pinned families: run-lifecycle (14), testing substrate (~75, incl.
  identity/laundering races each with a dedicated regression test), phase-1
  cluster (~40 incl. `test_phase1_partial_e2e` chaining guard → wheel pick →
  pin → assignment → path-sync over fixture git repos).
- Repo-neutrality: leak-scan ceilings unchanged; `rebase_engine/` is clean.
- Parity: behavior-level parity pinned per module (walk order, double-probed
  baseline fallback, sed-equivalent pin edits, decision JSON schema);
  byte-level goldens (prompts, request payloads, shell command echo) land in
  PR4b/PR5 per Rev 8.

## 8. Validation, staged enablement, rollback (unchanged from Rev 8)

Controlled comparison (frozen SHAs, restored knowledge snapshots, isolated
clones, separate validation branches); one external baseline run + one
supervised v3 full run; gate = deterministic harness green + live outcome
equivalence + 25% wall-clock bound + human-signed COMPARISON.md. Staged soak:
3 clean `report_only` nightlies (semantic diffs vs frozen baseline) → 2 clean
`local_ci` runs → 2 supervised full runs before unsupervised full. Rollback =
v1 backend or fresh external run; rehearsed timed (<30 min) before PR6; abort
criteria recorded in the RUNBOOK.

## 9. Top open risks

1. Dual command source false-pass (shell §10 slug → empty command → rc=0) —
   surfaced by shell-golden into `DRIFT_TRIAGE.md` (PR5), decided pre-cutover.
2. Push crash windows — PR3's write-ahead log + exact reconciliation.
3. Agent-mutation runs — risk reduction only (scrub, scratch clones, pushurl
   friction); the control is the Decision-5 recorded risk acceptance; OS
   sandboxing stays future hardening.
4. Validation sample size — deterministic harness is primary evidence; ≥7
   live data points before retirement.
