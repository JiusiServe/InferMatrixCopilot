---
name: fix-stale-test-path-collection-error-after-rename
description: Pipeline test fails rc=4/rc=5 "file or directory not found" / "collected 0 items" because config.sh CI_TEST_CMD points at a test file upstream renamed (*_expansion.py / *_tts.py) or moved; postmortem misreads it as a SILENT EXIT (OOM) and burns 3 GPU retries before hard-pausing.
trigger: Test log shows "ERROR: file or directory not found:" or "ERROR: not found:" or "collected 0 items" / "no tests ran"; rc=4 or rc=5; postmortem labels it "SILENT EXIT — child SIGKILL (OOM)". The referenced test file does NOT exist on disk.
modules: [online_serving, model_executor]
status: active
created_at: 2026-07-11
last_used_at: 2026-07-11
run_count: 6
---

## Diagnose
1. Grep the failing test log for `ERROR: file or directory not found:` / `ERROR: not found:` / `collected 0 items` / `no tests ran`. If present, this is a COLLECTION/PATH error, **not** OOM — ignore any `[postmortem] SILENT EXIT (OOM/SIGKILL)` footer (that classifier fires whenever there is no pytest traceback, which a collection error also lacks).
2. Confirm the file is actually missing: `ls /rebase/vllm-omni/<path-from-the-pytest-command>`.
3. Determine what happened to it upstream (vllm-omni's own `origin/main`):
   - Renamed/consolidated? `git -C /rebase/vllm-omni cat-file -e origin/main:<path>` → absent, but the `*_expansion.py` / `*_tts.py` sibling exists (test-layout refactors #2556, #4354 renamed `test_foo.py` → `test_foo_expansion.py` / `test_foo_tts.py`).
   - Moved to another dir? `find /rebase/vllm-omni/tests -name <basename>` finds it elsewhere.
   - Deleted and consolidated into a different tier? The survivor uses a different marker (e.g. `slow`) and runs in a different job.
4. This is a config bug in the rebase agent's manifest, not a vllm-omni model bug.

## Fix
Correct the path in `agent/config.sh` `CI_TEST_CMD` (never patch vllm-omni):
- **Renamed:** repoint to the current filename — `test_sd3.py`→`test_sd3_expansion.py`, `test_voxcpm2.py`→`test_voxcpm2_tts.py`, etc. Keep the same marker/run-level unless the survivor's markers changed.
- **Moved:** update the directory prefix (same basename).
- **Deleted + retiered upstream:** the merge-tier job no longer exists at that tier. **Retire it** — prefix `# STALE: ` on the slug in EVERY map (LOCAL_CI_TESTS, CI_TEST_LABEL, CI_TEST_SOURCE, CI_TEST_CMD, CI_TEST_TIMEOUT_SEC, min-gpus, hw, module). If a full_model/nightly job already runs the `*_expansion.py` survivor, coverage is preserved there.
- Scan for siblings that will fail the same way: for every `tests/**/*.py` in `CI_TEST_CMD`, check it exists on disk; fix all in one pass.

The guardrails now in place (do not re-break them): `agent/test_manifest.py::_validate_file_paths` is rename-aware (git rename map + canonical-stem fallback stripping `_expansion`/`_tts`), and `agent/lib/test_runner.sh::_append_silent_log_footer` emits a `COLLECTION/PATH ERROR` footer for rc=4/5 instead of the OOM footer.

## Verification
```bash
cd /rebase/vllm-omni && /rebase/.venv/bin/python -m pytest --collect-only -q <corrected-path>
```
Expect `rc=0` and `N tests collected` (not `collected 0 items`). Re-run the pipeline test; it should now execute rather than fail at collection.

## Anti-patterns
- **DO NOT re-create an upstream-deleted test file** to satisfy the stale config path (an earlier run hand-wrote `tests/e2e/online_serving/test_hunyuan_video_15.py` to match config.sh). It re-introduces coverage upstream deliberately removed, duplicates the `*_expansion.py` survivor, and conflicts on every future rebase. Fix config.sh instead.
- **DO NOT treat rc=4/rc=5 "collected 0 items" as OOM** and retry on GPU — the outcome never changes; it wastes 3 retries and hard-pauses the rebase.
- **DO NOT lower the pytest marker filter blindly** to force a `slow`/`full_model` survivor into a merge job — that changes CI cost/tiering against upstream intent.
