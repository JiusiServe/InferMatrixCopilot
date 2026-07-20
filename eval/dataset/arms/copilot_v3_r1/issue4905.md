# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

> ⚠ draft shipped with caveats — agent self-assessed confidence: high; verify before relying on it.

### Root cause
PR #4834 added `_level2_sleeping` flag and `NotImplementedError` guard in `wake_up()` at `vllm_omni/entrypoints/async_omni.py:953` as an intentional fix for #4473 Repro A. The guard correctly prevents silent output corruption after level-2 sleep. However, `test_multistage_sleep_h100` at `tests/entrypoints/test_omni_sleep_mode.py:547` was not updated — it still called `sleep(level=2)` followed by `wake_up()`, triggering the new guard.

### Fix
Change `sleep(level=2)` to `sleep(level=1)` in `test_multistage_sleep_h100`. The test validates multi-stage sleep/wake lifecycle, not level-2 semantics. Level-2 wake-is-unsupported behavior is already covered by `test_level2_sleep_wake_raises` (added in the same PR #4834).

### Workaround
Use `sleep(level=1)` instead of `level=2` for any test or workflow that needs to sleep then wake up. Level-2 is GPU-weight-discard; wake from level-2 is not yet implemented.

### Preconditions
`enable_sleep_mode=True` must be set on the engine. Level-1 sleep offloads weights to CPU RAM and supports fast DMA restore via `wake_up()`.

### Verification
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v

### Prevention
Add a CI pre-merge check: when a PR adds a new `NotImplementedError` or changes a control-plane contract (sleep/wake), grep for all test-level callers of the affected API and flag any that don't account for the new error path. Alternatively, add the `model-adaptation-review` skill's checklist item: 'existing e2e tests using the modified API are updated or explicitly marked as regression tests for the new behavior.'

### Disposition
close

### Additional context
## Root Cause

This is a **test-vs-implementation mismatch** introduced by PR #4834 (merge of the #4473 sleep-mode bugfix).

PR #4834 intentionally made `AsyncOmni.wake_up()` raise `NotImplementedError` after `sleep(level=2)`, because level-2 discards weights from GPU and the data-plane reload path is not yet implemented. This was the correct fix for #4473 Reproduction A (silent output corruption after level-2 sleep/wake).

However, the existing test `test_multistage_sleep_h100` was not updated to reflect this behavioral change. It called:

```python
acks = await engine.sleep(stage_ids=[0, 1], level=2)
# ...
await engine.wake_up(stage_ids=[0, 1])  # ← now raises NotImplementedError
```

**Evidence**: `NotImplementedError` originates from `async_omni.py:953` — the guard added by PR #4834 checking `self._level2_sleeping`.

## Fix

Change the sleep level in `test_multistage_sleep_h100` from `level=2` to `level=1`:

```diff
-        acks = await engine.sleep(stage_ids=[0, 1], level=2)
+        acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

The test's purpose is to validate the multi-stage sleep → wake → generate lifecycle (not level-2 semantics). Level-2 wake_is_not_supported_ behavior is already covered by the dedicated regression test `test_level2_sleep_wake_raises` (added in the same PR).

This fix appears to already be present in the current `main` checkout. If the CI is still failing at an older commit, cherry-pick or rebase to the fixed version.

## Verification

```bash
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v --co
```

## Prevention

When a PR introduces a new intentional error path (especially `NotImplementedError`), grep the repo for all callers of the affected API (`sleep` + `wake_up`) in tests to ensure they are updated or explicitly marked as regression tests for the new behavior.
