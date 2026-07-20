# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

> ⚠ draft shipped with caveats — agent self-assessed confidence: high; verify before relying on it.

### Root cause
test_multistage_sleep_h100 in tests/entrypoints/test_omni_sleep_mode.py used engine.sleep(level=2) followed by engine.wake_up(), but PR #4834 intentionally made wake_up() after sleep(level=2) raise NotImplementedError at vllm_omni/entrypoints/async_omni.py:945. The test was not updated to match the new API contract.

### Fix
In tests/entrypoints/test_omni_sleep_mode.py, function test_multistage_sleep_h100, change `engine.sleep(stage_ids=[0, 1], level=2)` to `engine.sleep(stage_ids=[0, 1], level=1)`. The current HEAD already has this fix applied.

### Workaround
Rerun CI with the fixed test file. The current checkout already shows level=1; if the fix has already been pushed, a simple CI rerun will pass.

### Preconditions
The level-1 sleep path must be functional on the test hardware (H100 / MI325). No other preconditions — this is a pure test parameter fix.

### Verification
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v --timeout=600

### Prevention
When adding a new guard that changes an existing API contract (like making wake_up() raise after level-2 sleep), search the test suite for all callers of the affected method to ensure they are updated. A grep for `sleep(.*level=2` in tests/ would have caught this before merge.

### Disposition
close / keep-open — if the fix (level=2→level=1) is already committed, close after confirmed CI pass. Reopen condition: if test_multistage_sleep_h100 still fails on CI with level=1 due to a different issue.

### Additional context
## Root Cause

This is a **test-only regression** introduced as a side effect of PR #4834. The PR intentionally added a guard in `AsyncOmni.wake_up()` that raises `NotImplementedError` when called after `sleep(level=2)`, because level-2 sleep discards weights entirely from GPU and reloading from disk is not yet implemented.

However, the existing test `test_multistage_sleep_h100` was written before this guard existed and called `sleep(level=2)` → `wake_up()`, which now correctly (and by design) hits the `NotImplementedError`.

**Evidence:**

- `vllm_omni/entrypoints/async_omni.py:945`: the guard added by PR #4834:
  ```python
  if getattr(self, "_level2_sleeping", False):
      raise NotImplementedError(
          "wake_up() after sleep(level=2) is not yet implemented: ..."
      )
  ```
- `tests/entrypoints/test_omni_sleep_mode.py` (failing commit): the test called `engine.sleep(stage_ids=[0, 1], level=2)` then `engine.wake_up(stage_ids=[0, 1])`

## Fix

Change `level=2` to `level=1` in `test_multistage_sleep_h100`:

```python
# Before (broken):
acks = await engine.sleep(stage_ids=[0, 1], level=2)

# After (fixed):
acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

**Why level=1 is correct:** The test's purpose is to verify a full sleep→wake→generate lifecycle. Level-1 offloads weights to CPU RAM and supports fast DMA restore via `wake_up()`, which is exactly the path this test should exercise. The level-2 path (wake_up raising `NotImplementedError`) is already tested by `test_level2_sleep_wake_raises` (line 412).

## Note

The current HEAD already shows `level=1` in this test, suggesting the fix may have already been committed. If so, a CI rerun of `tests/entrypoints/test_omni_sleep_mode.py` should confirm resolution. If not, the one-line change above is all that's needed.
