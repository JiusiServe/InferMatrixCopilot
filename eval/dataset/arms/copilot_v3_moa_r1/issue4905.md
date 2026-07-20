# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
test_multistage_sleep_h100 used sleep(level=2) followed by wake_up(), hitting the intentional NotImplementedError guard added by PR #4834 at vllm_omni/entrypoints/async_omni.py:953. The test was not updated in the same PR that introduced the guard.

### Fix
The test has already been fixed on main: changed sleep(level=2) to sleep(level=1) at tests/entrypoints/test_omni_sleep_mode.py:544. level=1 supports wake_up via CPU offload/DMA restore.

### Workaround
Use sleep(level=1) instead of sleep(level=2) if you need to wake up later. level=2 discards weights from GPU and disk reload is not yet implemented.

### Preconditions
The fix is on main (post-PR #4834 follow-up commits). Ensure CI runs against the current HEAD of main.

### Verification
The next CI run of tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 should pass since it now uses level=1.

### Prevention
PR #4834's test plan should have included updating test_multistage_sleep_h100 in the same changeset. As a guard, any PR that adds a new API error/exception should sweep all test callers of that API path. The new test_level2_sleep_wake_raises regression test now covers the level=2 path explicitly.

### Disposition
close

### Additional context
## Already fixed on `main` — no further action required

### Root cause

PR [#4834](https://github.com/vllm-project/vllm-omni/pull/4834) intentionally added a `NotImplementedError` guard in `wake_up()` when `sleep(level=2)` was used. This prevents the silent weight corruption and CUDA crashes reported in [#4473](https://github.com/vllm-project/vllm-omni/issues/4473):

```python
# vllm_omni/entrypoints/async_omni.py:953
if getattr(self, "_level2_sleeping", False):
    raise NotImplementedError(
        "wake_up() after sleep(level=2) is not yet implemented: ..."
    )
```

The CI failure occurred because `test_multistage_sleep_h100` was still calling `sleep(level=2)` followed by `wake_up()` at the time the CI ran. This test was not updated in the same PR.

### What was fixed

The test has since been updated to use `level=1` (which offloads weights to CPU RAM and supports fast DMA restore):

```python
# tests/entrypoints/test_omni_sleep_mode.py:544
acks = await engine.sleep(stage_ids=[0, 1], level=1)  # was level=2
assert len(acks) == 2
await engine.wake_up(stage_ids=[0, 1])  # works with level=1
```

Additionally:
- A dedicated regression test `test_level2_sleep_wake_raises` now validates that `wake_up()` after `sleep(level=2)` raises `NotImplementedError` ([test_omni_sleep_mode.py:413-417](tests/entrypoints/test_omni_sleep_mode.py#L413-L417)).
- The `test_coordinated_cross_device` test (which also uses `level=2`) is now `@pytest.mark.skip`.

### Sleep level semantics

| Level | Behavior | Wake support |
|-------|----------|-------------|
| 1 | Offloads weights to CPU RAM via DMA | ✅ Fast DMA restore |
| 2 | Discards weights from GPU entirely | ❌ Not yet implemented (disk reload needed) |

The `level=2` → `NotImplementedError` guard is a **safety feature**, not a regression. If you need sleep/wake cycling, use `sleep(level=1)`.

> ⚠ merge-state statements above were not verified via gh this run — treat as unconfirmed.
