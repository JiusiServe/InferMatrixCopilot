---
name: entrypoint-h100-timeout-1800s-runner-mismatch
description: Entrypoint tests time out (local rc=124 or Buildkite job state timed_out) with ALL executed tests passing. Budget problem, not a code bug — fix timeouts (local three-layer 7200s; CI timeout_in_minutes), never dispatch a code-debug agent.
trigger: entrypoint_test_with_h100 / entrypoint_test_with_l4 times out — local exit_code=124 or Buildkite job timed_out. ALL tests PASS (0 FAILED).
modules: [online_serving]
status: active
created_at: 2026-06-06
last_used_at: 2026-07-12
run_count: 55
---

## Diagnose
1. Check exit_code — 124 (local bash timeout) or Buildkite job state `timed_out` = timeout kill
2. Scan log for PASSED vs FAILED — all executed tests pass, 0 failed; the log shows fresh output (model loading / warmup) right up to the kill. If output went silent long before the kill, it is a HANG (different problem — debug it)
3. Local: check "TIMEOUT: test ... exceeded NNNs" — if NNN < 7200, phase3.py used a stale env value
4. CI: check the job duration against `timeout_in_minutes` in `.buildkite/test-merge.yml` — killed at exactly the budget

## Root Cause
The entrypoint suites relaunch a fresh OmniServer per test class (~30 model
loads on H100, including ten ~27.5 GiB Bagel loads in the sleep-mode tests).
Checkpoint-load I/O on the CI runners varies heavily with node page-cache
state: measured `Model loading took` totals for the same H100 job swing
34–43 min run-to-run (builds 2648/2650/2651/2655 — main times out on this
too; it is NOT a rebase or vLLM-version regression, and prefetch behavior is
identical across wheels). Any budget sized to the fast case fails on the slow
case.

**Local three layers of timeout**, all must be 7200s:
1. **Python-level** (phase3.py `_run_single_test`): subprocess timeout from `TEST_TIMEOUT_SEC` env — stale parent value kills the test prematurely.
2. **Bash-level** (test.sh): `timeout "$job_timeout"` from `CI_TEST_TIMEOUT_SEC[$key]:-$TEST_TIMEOUT_SEC`.
3. **Engine init** (test fixtures): `init_timeout` in `AsyncOmni()` calls.

**CI layer**: `timeout_in_minutes` in `.buildkite/test-merge.yml` — raised to
H100=90 / L4=45 in PR #5038 (align) / #5039 (main). The L4 job additionally
pays up to ~11 min for a cold docker image pull before pytest starts.

## Fix
Local (all three layers):
1. `agent/orchestrator.py` after `_export_all_settings(settings)`: `os.environ["TEST_TIMEOUT_SEC"] = "7200"`
2. `agent/config.sh`: `["entrypoint_test_with_h100"]=7200` in CI_TEST_TIMEOUT_SEC and default `TEST_TIMEOUT_SEC="${TEST_TIMEOUT_SEC:-7200}"`
3. `agent/subgraphs/phase3.py` `_run_single_test()`: force `env["TEST_TIMEOUT_SEC"] = "7200"`
4. `tests/entrypoints/test_omni_sleep_mode.py` llm_engine fixture: `init_timeout=900`

CI: raise `timeout_in_minutes` for the entrypoint jobs in
`.buildkite/test-merge.yml` (H100 90, L4 45 as of 2026-07-12). The monitor now
auto-classifies progressing timeouts as `budget_timeout`
(`_is_budget_timeout` in `agent/buildkite/monitor.py`) and will NOT dispatch
a debug agent — if you see a `budget_timeout` in the Phase 4 report, the fix
is in the pipeline YAML, not in code.

## Verification
- Local: re-run the slug via `bash agent/tasks/90_run_pipeline_tests.sh entrypoint_test_with_h100` — completes (~60-70 min on H100 hardware) with all tests passing.
- CI: Buildkite entrypoint jobs finish within the raised budgets (validation build: vllm-omni-rebase #2659).

## Anti-patterns
- Dispatching an SDK code-debug agent at a `timed_out` job whose tests were all passing (build 2655 burned a debug round editing `qwen3_code_predictor.py` for nothing).
- Rebuilding/retrying the same over-budget job hoping for fast runner I/O — a coin flip that costs an hour per flip.
- "Verifying" a fix by re-running a test the GPU gate skips (needs 4 GPUs, have 2) — a skip proves nothing (fixed in phase3.py `_shell_skipped` timestamp-prefix bug, 2026-07-12).
- Blaming the vLLM wheel version from a single build per branch — pull `Model loading took` distributions from several builds first.
