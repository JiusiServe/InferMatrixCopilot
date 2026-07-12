# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4905, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

This is **not a regression bug** — it's the intended behavior introduced by **PR #4834** ([Bugfix][sleep mode]: guard generation on partial wake and ensure wake idempotency).

The guard that raises `NotImplementedError` lives in:
- **`vllm_omni/entrypoints/async_omni.py:953`** — the `wake_up()` method checks `_level2_sleeping` (set after `sleep(level=2)`) and deliberately raises:

```python
if getattr(self, "_level2_sleeping", False):
    raise NotImplementedError(
        "wake_up() after sleep(level=2) is not yet implemented: weights were "
        "discarded from GPU and reloading from disk is not yet supported. "
        "Use sleep(level=1) instead, which offloads weights to CPU RAM "
        "and supports fast DMA restore."
    )
```

This was the fix for **issue #4473 Repro A**: before PR #4834, calling `sleep(level=2)` then `wake_up()` would *silently* produce corrupted output (e.g., `"!!!!!!!!!!!"`). Now it raises a clear `NotImplementedError` at the Python control-plane layer before any CUDA kernel can access freed memory.

The test `test_multistage_sleep_h100` (at `tests/entrypoints/test_omni_sleep_mode.py`, originally around line 540) was calling:
```python
acks = await engine.sleep(stage_ids=[0, 1], level=2)   # ← wrong level
await engine.wake_up(stage_ids=[0, 1])                   # ← hits NotImplementedError
```

The dedicated regression test `test_level2_sleep_wake_raises` (line 412) already correctly validates that `sleep(level=2)` + `wake_up()` raises `NotImplementedError`.

## Fix

Change `level=2` → `level=1` in `test_multistage_sleep_h100`:

```python
acks = await engine.sleep(stage_ids=[0, 1], level=1)
```

**Why:** Level-1 offloads weights to CPU RAM and supports `wake_up()` via fast DMA restore. Level-2 discards weights from GPU entirely; reloading from disk is not yet implemented (tracked as future work). The test intends to exercise a full sleep/wake cycle with inference verification, which level-1 supports.

## Current Status

The live checkout (`/rebase/vllm-omni`) already shows `level=1` in the test, so the fix appears to have already landed on `main`. A CI re-run should pass.

## Related
- **PR #4834** — introduced the level-2 guard (merged)
- **Issue #4473** — original bug: silent corruption / CUDA illegal memory access on partial wake
- **Test `test_level2_sleep_wake_raises`** — validates expected `NotImplementedError` for level-2

**Disposition:** close
