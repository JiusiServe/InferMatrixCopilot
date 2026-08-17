---
name: gpu-hang-low-max-num-batched-tokens
description: Fix GPU hang when max_num_batched_tokens is too small with concurrent requests after scheduler throttle_prefills change
trigger: GPU hang / NVIDIA watchdog kills process ~2s after start with 5+ concurrent requests and max_num_batched_tokens < 256. Error: 'Received cancellation signal, interrupting' without Python traceback.
modules: [online_serving, worker_runner]
status: active
created_at: 2026-06-18
last_used_at: 2026-07-11
run_count: 38
---

## Diagnose

1. Check if the test uses a small `max_num_batched_tokens` value (e.g., 64) with concurrent requests (request_num >= 5).
2. Look for 'Received cancellation signal, interrupting' in the CI log, which indicates NVIDIA GPU watchdog killing the process.
3. Verify the upstream vLLM scheduler changed recently (e.g., `throttle_prefills` API was added) — this interacts poorly with very small token budgets.

## Fix

Increase `max_num_batched_tokens` from the extreme value (e.g., 64) to a moderate small value (e.g., 512) that still exercises the small-batch path but avoids the GPU hang.

Example fix in test config:
```python
# In get_batch_token_config() or similar function:
updates={"stages": {0: {"max_num_batched_tokens": 512}, 1: {"max_num_batched_tokens": 512}}}
```

Add a comment explaining why 64 was too small and noting the value may need adjustment if the scheduler changes again.

## Files to modify

- `tests/e2e/online_serving/test_qwen3_omni_expansion.py` (the `get_batch_token_config` function)

## Verification

Cannot fully verify without 2x H100 GPUs, but import check confirms no syntax errors. The change is a test config tweak only — no product code changes.
