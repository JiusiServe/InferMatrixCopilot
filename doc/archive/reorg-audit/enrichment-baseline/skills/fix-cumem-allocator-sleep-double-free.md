---
name: fix-cumem-allocator-sleep-double-free
description: Fix CUDA invalid argument error at cumem_allocator.cpp:235 during engine shutdown by using release_pools() instead of sleep()
trigger: CUDA Error: invalid argument at cumem_allocator.cpp:235 during engine shutdown, or watchdog kills test suite (rc=143) after all tests PASS with CUDA error in shutdown cleanup
modules: [online_serving, worker_runner]
status: retired
created_at: 2026-07-07
last_used_at: 2026-07-07
run_count: 2
---

> ⚠️ **RETIRED / SUPERSEDED by `fix-cumem-cuda-double-free-gc-atexit`.**
> This skill's fix (swap `allocator.sleep()` → `release_pools()` at the engine
> shutdown call site) is incomplete, and its rationale is wrong: it claims the
> free-callback returns a **null** handle on CUDA for asleep entries, but the
> callback actually returns a **stale** handle on CUDA (the ROCm-only guard is the
> real bug), so the double-free still recurs via the atexit GC path. Use the
> callback-patch skill instead — it fixes the root cause for all paths. Kept only
> for history; not surfaced to the agent (`status: retired`).

## Diagnose

1. Check if the test suite reports rc=143 (SIGKILL by watchdog) even though all individual tests PASS
2. Search for `CUDA Error: invalid argument at /workspace/csrc/cumem_allocator.cpp:235` in the log
3. Line 235 corresponds to `cuMemRelease(*p_memHandle)` in `unmap_and_release()`
4. This indicates CuMemAllocator.sleep() was called on already-slept entries, causing a double-free

## Root Cause

`CuMemAllocator.sleep()` (in upstream `vllm/vllm/device_allocator/cumem.py`) is NOT idempotent. When called on entries with `is_asleep=True`:

1. The C code calls `free(p_memHandle)` during the first `sleep()` (frees the malloc'd pointer)
2. But `data.handle[3]` still holds the old integer value of the freed pointer
3. A second `sleep()` call passes the stale pointer to `cuMemRelease`, which fails with CUDA_ERROR_INVALID_VALUE

## Fix

In `vllm_omni/engine/async_omni_engine.py`, replace `allocator.sleep()` with `allocator.release_pools()` in the shutdown code:

```python
# Before (line ~1536):
allocator.sleep()

# After:
allocator.release_pools()
```

`release_pools()` is the designed cleanup path: it drops MemPool references and triggers GC. The GC invokes `_python_free_callback` for each entry. For asleep entries, the callback returns a null handle (0 on CUDA, [] on ROCm), making the C extension's null-pointer check (`p_memHandle != nullptr`) correctly skip the double-free.

## Files to modify

- `vllm_omni/engine/async_omni_engine.py` (the shutdown CuMem cleanup section)

## Verification

1. Run `test_llm_sleep_ack` and `test_duplicate_wake_is_idempotent` (the regression tests that specifically test sleep mode shutdown)
2. Verify no CUDA errors in stderr output
3. Check all tests PASS without watchdog killing the process
