---
name: fix-cumem-cuda-double-free-gc-atexit
description: Fix CuMemAllocator double-free on CUDA during atexit shutdown — patch _python_free_callback to handle asleep entries on all platforms, not just ROCm.
trigger: CUDA Error: invalid argument at cumem_allocator.cpp:235 during engine shutdown after test_llm_sleep_ack or any test that uses sleep mode (enable_sleep_mode=True). All tests PASS but rc=143 from watchdog due to double-free in EngineCore subprocess atexit cleanup.
modules: [online_serving]
status: active
created_at: 2026-07-08
last_used_at: 2026-07-11
run_count: 5
---

## Diagnose

1. Check for `CUDA Error: invalid argument at /workspace/csrc/cumem_allocator.cpp:235` in the log
2. Look for `CuMemAllocator: sleep freed` preceding the error — confirms sleep was called
3. Check if all individual tests PASS and the failure is rc=143 (watchdog kill)
4. The error occurs in the EngineCore subprocess (StageEngineCoreProc) during atexit cleanup

## Root Cause

`CuMemAllocator._python_free_callback` at `vllm/vllm/device_allocator/cumem.py:206`:
```python
if data.is_asleep and current_platform.is_rocm():
```

The upstream commit `68afd78897` only added the safe empty-handle return for ROCm.
On CUDA, the callback returns the stale handle, causing `cuMemRelease` on
already-freed memory.

The sequence:
1. Worker calls `allocator.sleep()` → `unmap_and_release(handle)` → `is_asleep=True`
2. EngineCore subprocess exits → Python atexit fires `_shutdown_singleton`
3. `release_pools()` → GC → `_python_free_callback` for asleep entries
4. On CUDA: returns stale handle → C extension calls `cuMemRelease` → ERROR

## Fix

In `vllm_omni/patch.py`, add `_patch_cumem_free_callback_cuda()` that
monkey-patches `CuMemAllocator._python_free_callback` to remove the
`current_platform.is_rocm()` condition:

```python
def _patch_cumem_free_callback_cuda() -> None:
    from vllm.device_allocator.cumem import CuMemAllocator
    
    def _patched_free_callback(self, ptr: int) -> tuple:
        data = self.pointer_to_data.pop(ptr)
        if data.cpu_backup_tensor is not None:
            data.cpu_backup_tensor = None
        if data.is_asleep:
            device, size, d_mem, _ = data.handle
            return (device, size, d_mem, [])
        torch.accelerator.synchronize(data.handle[0])
        return data.handle
    
    CuMemAllocator._python_free_callback = _patched_free_callback

_patch_cumem_free_callback_cuda()
```

The change is simply removing `and current_platform.is_rocm()` — the behavior
is the same on both platforms since `sleep()` calls `unmap_and_release()` everywhere.

## Files to modify

- `vllm_omni/patch.py` — add `_patch_cumem_free_callback_cuda()` function + call it

## Verification

```python
import vllm_omni.patch
from vllm.device_allocator.cumem import CuMemAllocator
import inspect
src = inspect.getsource(CuMemAllocator._python_free_callback)
assert "is_rocm" not in src, "ROCm-only guard still present"
print("OK: Patched correctly")
```

## Anti-patterns

- Do NOT rely solely on swapping `allocator.sleep()` → `allocator.release_pools()` at the
  engine-shutdown call site (the retired `fix-cumem-allocator-sleep-double-free` approach).
  That contradicts the real root cause: `release_pools()` still drives GC →
  `_python_free_callback`, which on CUDA returns the **stale** handle for asleep entries
  (it does NOT return a null handle on CUDA — only ROCm), so the double-free recurs via the
  atexit path in the EngineCore subprocess. Patch the callback (this skill) — it is the single
  root fix that covers every path (explicit `sleep()`, `release_pools()`, and atexit GC).
- This is the **canonical** skill for `cumem_allocator.cpp:235` double-free on sleep-mode shutdown.
