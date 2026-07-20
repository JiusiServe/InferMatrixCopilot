# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
PR #4834 added an intentional NotImplementedError guard for wake_up() after sleep(level=2) at vllm_omni/entrypoints/async_omni.py:953-958, but the existing test_multistage_sleep_h100 in tests/entrypoints/test_omni_sleep_mode.py continued to call sleep(level=2) + wake_up(), triggering the guard in CI.

### Fix
Change sleep(level=2) to sleep(level=1) in test_multistage_sleep_h100. Already implemented by merged PR #4912.

### Verification
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -v --tb=short (on main after PR #4912)

### Prevention
When adding new guards or NotImplementedError raises, sweep all in-repo consumers (tests, examples, docs) for the old behaviour. Use grep for the old pattern before merging; the 'pr-review-breaking-changes' skill documents this.

### Disposition
close

### Additional context
## Root Cause

PR #4834 intentionally added a `NotImplementedError` guard at `vllm_omni/entrypoints/async_omni.py:953` to prevent calling `wake_up()` after `sleep(level=2)`. Level‑2 sleep discards weights from GPU and reloading from disk is not yet implemented, so the guard corrects silent corruption and CUDA crashes reported in #4473. However, the existing test `test_multistage_sleep_h100` in `tests/entrypoints/test_omni_sleep_mode.py` still used `sleep(level=2)` followed by `wake_up()`, hitting the new guard and causing the CI failure.

## Fix

**PR #4912** (already merged) changes the test to use `sleep(level=1)`. Level‑1 sleep offloads weights to CPU RAM and supports fast DMA restore via `wake_up()`, which is the intended behavior for this multi‑stage sleep/wake test.

```python
# Before: acks = await engine.sleep(stage_ids=[0, 1], level=2)
# After:  acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

## Remaining level=2 Uses Are Safe

- `test_coordinated_cross_device`: already `@pytest.mark.skip`, not running in CI.
- `test_level2_sleep_wake_raises`: correctly asserts `pytest.raises(NotImplementedError)` — the regression test for this exact guard.

## Disposition

The issue is resolved on `main`. **Close.**

> ⚠ merge-state statements above were not verified via gh this run — treat as unconfirmed.
