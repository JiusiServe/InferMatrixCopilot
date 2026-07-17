---
name: buildkite-skipped-build-rebuild-fratricide
description: Phase-4 CI builds on the vllm-omni-rebase pipeline get state=skipped (only ":pipeline: Load pipeline" job) because the push's webhook build lands ~0.5s later and skip_queued_branch_builds kills the older API build; and any NEW build creation (including PUT /rebuild) cancels the RUNNING build on the branch within ~200ms via cancel_running_branch_builds. A rebuild also CREATES a new build — monitoring the original URL watches a corpse while the rebuild runs unobserved.
trigger: Buildkite build state is "skipped" or "not_run" with 0-1 jobs; monitor reports "incomplete (:pipeline: Load pipeline)" for hours; a running build (often the scheduled nightly) shows canceled with finished_at within ~1s of another build's created_at; "Incremental rebuild triggered" but the watched build never changes state.
modules: []
status: active
created_at: 2026-07-11
last_used_at: 2026-07-11
run_count: 4
---

## Diagnose
1. Get the build: `GET /v2/organizations/vllm/pipelines/vllm-omni-rebase/builds/<N>`. If `state` is `skipped` or `not_run`, the pipeline REFUSED to run it — it will never produce jobs. Do not keep polling it; do not classify its Load-pipeline job as a retryable "incomplete".
2. List sibling builds at the same commit (**full 40-char SHA — short SHAs silently return nothing**): `GET .../builds?branch=<branch>&commit=<full-sha>`. Typical pattern after an agent push+trigger: our `api` build `skipped`, a `webhook` build `not_run` (created ~0.5s after ours; its creation is what skipped ours), and possibly a `schedule`/later `api` build that actually ran.
3. To confirm a fratricide cancelation: compare the canceled build's `finished_at` with every other build's `created_at` on the branch — a gap under ~1s means the new build's creation canceled it (pipeline has `cancel_running_branch_builds=true` with an EMPTY filter; verified 2026-07-11: rebuild #2629's creation canceled running nightly #2627 in 200ms, and #2630's creation then canceled running #2629).
4. Root cause is pipeline configuration: `skip_queued_branch_builds=true` AND `cancel_running_branch_builds=true` with empty branch filters, on a pipeline whose default branch (`dev/vllm-align`) runs full 88-job suites.

## Fix
Code-side (landed on feat/knowledge-layer, commits 8ae5268 + 8c1f8d2 — verify present before re-implementing):
1. Treat `skipped`/`not_run` as instantly terminal (`BUILD_NO_RUN_STATES` in `agent/buildkite/monitor.py`); `MonitorReport.was_skipped` blocks `is_clean_pass`.
2. After pushing, wait ~60s BEFORE `create_build` so the push's webhook build lands first — our API build is then the newest and nothing skips it (`phase4.py` "webhook build to settle").
3. If our build still lands in a no-run state, adopt the sibling that actually runs: `BuildkiteClient.find_build_for_commit(full_sha, branch, exclude_numbers=(ours,))`.
4. Never `PUT /rebuild` a no-run build, never rebuild while a DIFFERENT commit's build is running on the branch (creation cancels it), adopt an active same-commit build instead, and when a rebuild does fire, monitor the NEW build URL returned in the response body — not the original.
Admin-side (the real fix, needs pipeline settings access): set `skip_queued_branch_builds_filter` and `cancel_running_branch_builds_filter` to exclude `dev/vllm-align` (e.g. `!dev/vllm-align`), or disable `cancel_running_branch_builds`.

## Verification
1. `pytest agent/tests/test_phase34_fixes.py -q` → the skipped-terminal, sibling-adoption, fratricide-guard, and rebuild-follows-new-build tests pass.
2. After a Phase-4 push+trigger, the orchestrator log shows either `Build #<N> (state=running...)` on OUR build, or `Adopting sibling build #<M>` — and never hours of `still ... (elapsed=...)` against a `skipped` build.
3. No build on the branch shows `canceled` with `finished_at` within 1s of a build the agent created.

## Anti-patterns
- Polling a `skipped`/`not_run` build until the monitor timeout, or counting its Load-pipeline job as a retryable incomplete job (burned 6-9h in the 07-07 and 07-09 runs).
- Rebuilding a skipped build "to retry flaky jobs" — the rebuild creates a NEW build whose creation cancels whatever is running on the branch (killed scheduled nightly #2627 mid-suite).
- Monitoring the original build URL after a rebuild — the rebuild's builds (#2629/#2630) ran the full suite unobserved while the agent watched skipped #2625.
- Querying `builds?commit=<short-sha>` — Buildkite requires the full 40-char SHA and returns an empty list otherwise, which looks like "no sibling exists".
- "Fixing" this in vllm-omni or the agent's test logic — it is Buildkite pipeline configuration plus trigger ordering, nothing else.
