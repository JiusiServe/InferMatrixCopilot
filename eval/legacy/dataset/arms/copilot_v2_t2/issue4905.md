# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

This is **not a product bug** — it's a **test parameter mismatch** introduced as a side effect of PR #4834.

### Mechanism

PR #4834 ([Bugfix][sleep mode]: guard generation on partial wake and ensure wake idempotency) added a safety guard in `AsyncOmni.wake_up()`:

- `vllm_omni/entrypoints/async_omni.py:947` — `sleep(level=2)` sets `self._level2_sleeping = True`
- `vllm_omni/entrypoints/async_omni.py:953` — `wake_up()` checks `_level2_sleeping` and raises `NotImplementedError` if True

This is **correct, intended behavior**: level-2 sleep discards weights from GPU entirely (they are not offloaded to CPU RAM), and reloading from disk is not yet implemented. Before #4834, calling `wake_up()` after `level=2` sleep would silently produce corrupted output (garbage tokens). The guard is the fix for that bug (issue #4473).

### Why the test failed

The pre-existing `test_multistage_sleep_h100` (at the failing commit `ddba6de`) called:
```python
acks = await engine.sleep(stage_ids=[0, 1], level=2)   # ← sets _level2_sleeping=True
await engine.wake_up(stage_ids=[0, 1])                   # ← raises NotImplementedError
```

PR #4834 did **not** modify `test_multistage_sleep_h100` — it only added three new regression tests (`test_level2_sleep_wake_raises`, `test_partial_wake_blocks_generate`, `test_duplicate_wake_is_idempotent`). The test was never updated to match the new API contract.

Note that `test_level2_sleep_wake_raises` (line 413) **correctly** expects `NotImplementedError` after `sleep(level=2)` — confirming this is the designed behavior for level-2.

## Fix

Change `level=2` to `level=1` in `test_multistage_sleep_h100`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

The test's intent is to verify the full sleep→wake→generate lifecycle for a 2-stage pipeline, which requires `level=1` (weights offloaded to CPU, DMA-restorable). Level-2 is deliberately not wakeable.

This fix is already present in the current working tree at `tests/entrypoints/test_omni_sleep_mode.py:536`.

## Workaround

If you need to run this test before the fix lands: use `sleep(level=1)` instead of `sleep(level=2)`. Level-1 offloads weights to CPU RAM and supports fast DMA wake-up; level-2 discards weights entirely and does not support wake-up.

## Verification

```bash
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v -k '1' --run-level=full_model
pytest tests/entrypoints/test_omni_sleep_mode.py::TestOmniSleepMode::test_level2_sleep_wake_raises -v
```

Both should pass: the first tests the working sleep/wake cycle (level=1), the second confirms that level-2 correctly rejects wake_up.

## Related

- PR #4834: [Bugfix][sleep mode] guard generation on partial wake and ensure wake idempotency
- Issue #4473: Original sleep-mode corruption/crash bug that #4834 fixed

## draft_answer

## Root Cause

This is **not a product bug** — it's a **test parameter mismatch** introduced as a side effect of PR #4834.

### Mechanism

PR #4834 ([Bugfix][sleep mode]: guard generation on partial wake and ensure wake idempotency) added a safety guard in `AsyncOmni.wake_up()`:

- `vllm_omni/entrypoints/async_omni.py:947` — `sleep(level=2)` sets `self._level2_sleeping = True`
- `vllm_omni/entrypoints/async_omni.py:953` — `wake_up()` checks `_level2_sleeping` and raises `NotImplementedError` if True

This is **correct, intended behavior**: level-2 sleep discards weights from GPU entirely (they are not offloaded to CPU RAM), and reloading from disk is not yet implemented. Before #4834, calling `wake_up()` after `level=2` sleep would silently produce corrupted output (garbage tokens). The guard is the fix for that bug (issue #4473).

### Why the test failed

The pre-existing `test_multistage_sleep_h100` (at the failing commit `ddba6de`) called:
```python
acks = await engine.sleep(stage_ids=[0, 1], level=2)   # ← sets _level2_sleeping=True
await engine.wake_up(stage_ids=[0, 1])                   # ← raises NotImplementedError
```

PR #4834 did **not** modify `test_multistage_sleep_h100` — it only added three new regression tests (`test_level2_sleep_wake_raises`, `test_partial_wake_blocks_generate`, `test_duplicate_wake_is_idempotent`). The test was never updated to match the new API contract.

Note that `test_level2_sleep_wake_raises` (line 413) **correctly** expects `NotImplementedError` after `sleep(level=2)` — confirming this is the designed behavior for level-2.

## Fix

Change `level=2` to `level=1` in `test_multistage_sleep_h100`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

The test's intent is to verify the full sleep→wake→generate lifecycle for a 2-stage pipeline, which requires `level=1` (weights offloaded to CPU, DMA-restorable). Level-2 is deliberately not wakeable.

This fix is already present in the current working tree at `tests/entrypoints/test_omni_sleep_mode.py:536`.

## Workaround

If you need to run this test before the fix lands: use `sleep(level=1)` instead of `sleep(level=2)`. Level-1 offloads weights to CPU RAM and supports fast DMA wake-up; level-2 discards weights entirely and does not support wake-up.

## Verification

```bash
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v -k '1' --run-level=full_model
pytest tests/entrypoints/test_omni_sleep_mode.py::TestOmniSleepMode::test_level2_sleep_wake_raises -v
```

Both should pass: the first tests the working sleep/wake cycle (level=1), the second confirms that level-2 correctly rejects wake_up.

## Related

- PR #4834: [Bugfix][sleep mode] guard generation on partial wake and ensure wake idempotency
- Issue #4473: Original sleep-mode corruption/crash bug that #4834 fixed

---

## Step diagnostics

### fetch

### draft
- **status**: success
- **summary**: The CI failure at commit ddba6de is a test mismatch: `test_multistage_sleep_h100` calls `sleep(level=2)` followed by `wake_up()`, but PR #4834 intentionally made `wake_up()` after `sleep(level=2)` raise `NotImplementedError` as a safety guard. The test should use `level=1` (which supports wake_up). The working tree already contains the fix.
- **findings**: ['Root cause: `test_multistage_sleep_h100` at the failing commit called `engine.sleep(stage_ids=[0, 1], level=2)` then `engine.wake_up(stage_ids=[0, 1])`, but PR #4834 added a `_level2_sleeping` flag that causes `wake_up()` to raise `NotImplementedError` — a deliberate guard against waking discarded weights.', 'PR #4834 (merged) introduced the `_level2_sleeping` flag in `AsyncOmni.sleep()` (set True at `async_omni.py:947` when `level==2`) and the guard in `AsyncOmni.wake_up()` (raises `NotImplementedError` at `async_omni.py:953` when `_level2_sleeping` is True). This is correct intended behavior: level-2 discards weights from GPU entirely, and reload from disk is not yet implemented.', 'PR #4834 added `test_level2_sleep_wake_raises` (the regression test at `test_omni_sleep_mode.py:413`) that explicitly expects `NotImplementedError` from `wake_up()` after `sleep(level=2)` — confirming this is by design.', "`test_multistage_sleep_h100` was not modified by PR #4834 (PR only added 41 lines of new tests, didn't touch that function), so the pre-existing `level=2` parameter became stale and incompatible with the new guard.", "The working tree on disk already shows `level=1` at `test_omni_sleep_mode.py:536` — a simple parameter fix that restores the test's intent (full sleep/wake lifecycle). The only remaining `level=2` uses in the test file are `test_coordinated_cross_device` (already `@pytest.mark.skip`-ed and doesn't call `wake_up`) and `test_level2_sleep_wake_raises` (explicitly expects the `NotImplementedError`)."]
- **files_read**: ['/rebase/vllm-omni/tests/entrypoints/test_omni_sleep_mode.py', '/rebase/vllm-omni/vllm_omni/entrypoints/async_omni.py']
- **files_modified**: []
- **tests_requested**: ["pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v -k '1' --run-level=full_model", 'pytest tests/entrypoints/test_omni_sleep_mode.py::TestOmniSleepMode::test_level2_sleep_wake_raises -v']
- **tests_run**: []
- **assumptions**: ['The current working tree (level=1) represents the intended fix and is not an accidental or incomplete edit', 'The CI ran against the commit ddba6de which predates the level=2→level=1 fix', 'No other test or production code path calls wake_up() after level=2 sleep']
- **blockers**: []
- **confidence**: high
- **failure_kind**: test_failure
- **next_action**: If the fix (level=2→level=1) is not yet in a PR, open one. Then trigger the full sleep mode CI suite (tests/entrypoints/test_omni_sleep_mode.py) to confirm green, particularly `test_multistage_sleep_h100` and `test_level2_sleep_wake_raises`.
- **answer_draft**: ## Root Cause

This is **not a product bug** — it's a **test parameter mismatch** introduced as a side effect of PR #4834.

### Mechanism

PR #4834 ([Bugfix][sleep mode]: guard generation on partial wake and ensure wake idempotency) added a safety guard in `AsyncOmni.wake_up()`:

- `vllm_omni/entrypoints/async_omni.py:947` — `sleep(level=2)` sets `self._level2_sleeping = True`
- `vllm_omni/entrypoints/async_omni.py:953` — `wake_up()` checks `_level2_sleeping` and raises `NotImplementedError` if True

This is **correct, intended behavior**: level-2 sleep discards weights from GPU entirely (they are not offloaded to CPU RAM), and reloading from disk is not yet implemented. Before #4834, calling `wake_up()` after `level=2` sleep would silently produce corrupted output (garbage tokens). The guard is the fix for that bug (issue #4473).

### Why the test failed

The pre-existing `test_multistage_sleep_h100` (at the failing commit `ddba6de`) called:
```python
acks = await engine.sleep(stage_ids=[0, 1], level=2)   # ← sets _level2_sleeping=True
await engine.wake_up(stage_ids=[0, 1])                   # ← raises NotImplementedError
```

PR #4834 did **not** modify `test_multistage_sleep_h100` — it only added three new regression tests (`test_level2_sleep_wake_raises`, `test_partial_wake_blocks_generate`, `test_duplicate_wake_is_idempotent`). The test was never updated to match the new API contract.

Note that `test_level2_sleep_wake_raises` (line 413) **correctly** expects `NotImplementedError` after `sleep(level=2)` — confirming this is the designed behavior for level-2.

## Fix

Change `level=2` to `level=1` in `test_multistage_sleep_h100`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

The test's intent is to verify the full sleep→wake→generate lifecycle for a 2-stage pipeline, which requires `level=1` (weights offloaded to CPU, DMA-restorable). Level-2 is deliberately not wakeable.
