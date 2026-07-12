# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Diagnosis

This is **not a bug** — it's the intended behavior of PR #4834 working correctly, combined with a stale test configuration that has since been fixed.

### Root cause

PR #4834 (merged at the time of this CI failure) added a deliberate safety guard in `AsyncOmni.wake_up()` (`vllm_omni/entrypoints/async_omni.py:945`):

```python
if getattr(self, "_level2_sleeping", False):
    raise NotImplementedError(
        "wake_up() after sleep(level=2) is not yet implemented: weights were "
        "discarded from GPU and reloading from disk is not yet supported. ..."
    )
```

This is **correct and intentional**. Sleep level 2 discards weights entirely from GPU VRAM (they are not offloaded to CPU RAM), so wake_up cannot restore them without a disk-reload mechanism, which is not yet implemented. Before PR #4834, calling wake_up after level-2 sleep would silently produce corrupted/garbage output (issue #4473 Repro A).

### Why the test failed

The test `test_multistage_sleep_h100` was calling:

```python
acks = await engine.sleep(stage_ids=[0, 1], level=2)   # ← should be level=1
...
await engine.wake_up(stage_ids=[0, 1])                  # ← raises NotImplementedError
```

The test should use **level=1**, which offloads weights to CPU RAM and supports fast DMA restore via wake_up. The correct invocation is:

```python
acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

### Current status: **Already fixed**

The current HEAD of the repository already has this correction applied. In `tests/entrypoints/test_omni_sleep_mode.py` line 545, the test now reads:

```python
acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

Additionally, PR #4834 also added `test_level2_sleep_wake_raises` (line 413) which explicitly tests that `wake_up()` after `sleep(level=2)` raises `NotImplementedError` — this is the correct regression test for the level-2 guard.

### Workaround (if you hit this manually)

If you're calling `sleep(level=2)` in your own code and need to wake up afterward, use `sleep(level=1)` instead:

```python
# Instead of:
await engine.sleep(stage_ids=[0, 1], level=2)

# Use:
await engine.sleep(stage_ids=[0, 1], level=1)
await engine.wake_up(stage_ids=[0, 1])  # works — DMA restore from CPU RAM
```

Level 2 wake-up support (disk reload) is tracked as future work.

### Verification

```bash
# Confirm the fix is in place:
grep -n 'level=1' tests/entrypoints/test_omni_sleep_mode.py | grep multistage
# Should show:  acks = await engine.sleep(stage_ids=[0, 1], level=1)

# Run the corrected test:
pytest tests/entrypoints/test_omni_sleep_mode.py::test_multistage_sleep_h100 -k 'tp_size=1' --run-level=full_model
```

## Resolution

This issue is already resolved in the current codebase. The test was corrected from `level=2` to `level=1`. No further changes are needed.

See also: PR #4834 (the bugfix that introduced the guard), issue #4473 (the original corruption/crash reports).

**Disposition:** close
