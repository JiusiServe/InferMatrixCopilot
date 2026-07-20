# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
In gpu_generation_model_runner.py:468 (and npu_generation_model_runner.py:488), the `async_chunk=False` branch of `sample_tokens()` previously set `inter_stage_outputs = None, multimodal_outputs = per_req_payloads`, starving the downstream stage of the full-payload data it needed. This was introduced by PR #4527 and caused the 300s timeout hang in Qwen3-TTS multi-stage (talker → code2wav) pipelines with `async_chunk: false`.

### Fix
Changed the `async_chunk=False` branch to `inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads` so the full payload ships to the next stage. Applied in both gpu_generation_model_runner.py (~line 468) and npu_generation_model_runner.py (~line 488), merged via rebase commit a560ed18.

### Preconditions
vLLM 0.24 or later (which includes the rebase commit a560ed18); both talker and code2wav stages must be healthy and correctly configured

### Verification
pytest tests/worker/test_gpu_ar_model_runner.py::test_sample_tokens_tail_only_prefix_cache_uses_staged_cpu_hidden_states -v (asserts inter_stage_outputs mirrors multimodal_outputs in async_chunk=False mode)

### Prevention
PR #4792 added a comment referencing both #4527 and the fix; the test `test_sample_tokens_tail_only_prefix_cache_uses_staged_cpu_hidden_states` enforces the non-async-chunk output contract going forward

### Disposition
close / the fix is already merged into the user's commit via the vLLM 0.24 rebase; reopen only if the hang persists after confirming the running binary is from commit 0899a1a or later

### Additional context
# `async_chunk: false` Multi-Stage Pipeline Hang — Already Fixed

Thanks for the detailed report. **This issue has already been fixed** and the fix is included in your current commit (0899a1a) via the vLLM 0.24 rebase.

## Root Cause

In the `sample_tokens()` method of both `gpu_generation_model_runner.py` and `npu_generation_model_runner.py`, the non-async-chunk code path was setting:

```python
inter_stage_outputs, multimodal_outputs = None, per_req_payloads
```

This was introduced by PR #4527 and caused the downstream stage (code2wav in the Qwen3-TTS pipeline) to receive **no inter-stage output**, leaving it waiting forever for input until the 300s timeout.

## Fix

PR #4792 changed the `async_chunk=False` branch to ship the full payload to the next stage:

```python
# vllm_omni/worker/gpu_generation_model_runner.py  (~line 468)
# vllm_omni/platforms/npu/worker/npu_generation_model_runner.py  (~line 488)
else:
    # non-async-chunk ships the full payload to the next
    # stage; #4527's (None, per_req_payloads) starved the downstream stage.
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

This fix was merged as part of the vLLM 0.24 rebase commit `a560ed184d9197855f1cccf46cb1cac87b0a7138`.

## What to Do

Since your commit `0899a1a` already includes the vLLM 0.24 rebase, the fix is already present. If you're still seeing the hang, double-check that:

1. Your deployment is actually running from this commit (check the server startup log for the SHA)
2. The deploy config's `async_chunk: false` is being read correctly (no YAML override interference)
3. Both the talker and code2wav stages are healthy and not stuck in initialization

## Verification

Run the unit test that covers the non-async-chunk output contract:
```bash
pytest tests/worker/test_gpu_ar_model_runner.py::test_sample_tokens_tail_only_prefix_cache_uses_staged_cpu_hidden_states -v
```

This test asserts that in `async_chunk=False` mode, `inter_stage_outputs` mirrors `multimodal_outputs` — confirming the full payload is shipped downstream.
