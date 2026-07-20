# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
In `GPUGenerationModelRunner.sample_tokens()` (gpu_generation_model_runner.py) and `GPUARModelRunner._build_omni_model_runner_output_from_snapshot()` (gpu_ar_model_runner.py), the `async_chunk: false` code path partitioned the per-request payload list into `(inter_stage_outputs=None, multimodal_outputs=<payload>)` — the `None` inter-stage outputs starved the downstream stage connector, causing the 300-second timeout. The fix (PR #4792) changes the non-async-chunk branch to pass the full payload as both fields: `inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads` (line 467) and `pooler_inter, pooler_client = pooler_output, pooler_output` (line 1813).

### Fix
Update to a commit that includes the vLLM 0.24 rebase (e.g. `a560ed184d9197855f1cccf46cb1cac87b0a7138`) or cherry-pick PR #4792 onto your current branch. The fix touches four runner files: `vllm_omni/worker/gpu_generation_model_runner.py`, `vllm_omni/worker/gpu_ar_model_runner.py`, `vllm_omni/platforms/npu/worker/npu_generation_model_runner.py`, `vllm_omni/platforms/npu/worker/npu_ar_model_runner.py`.

### Workaround
Use `async_chunk: true` (the default in `vllm_omni/deploy/qwen3_tts.yaml`), which the reporter has already confirmed works.

### Preconditions
The reporter must be on a commit that includes the vLLM 0.24 rebase (commit `a560ed184d9197855f1cccf46cb1cac87b0a7138` or later) or have cherry-picked PR #4792. No hardware or model changes are required.

### Verification
pytest tests/worker/test_gpu_ar_model_runner.py::test_sample_tokens_tail_only_prefix_cache_uses_staged_cpu_hidden_states -xvs

### Prevention
Add an end-to-end integration test for multi-stage talker→code2wav pipelines with `async_chunk: false` to catch regressions in the inter-stage payload routing before release. The existing runner-level unit test covers the logic but not the full connector lifecycle.

### Disposition
close

### Additional context
## Root cause

When `async_chunk: false`, the inter-stage connector payload was incorrectly dropped to `None` instead of being forwarded to the downstream stage. This affected two key runner methods:

- **`GPUGenerationModelRunner.sample_tokens()`** — `vllm_omni/worker/gpu_generation_model_runner.py`
- **`GPUARModelRunner._build_omni_model_runner_output_from_snapshot()`** — `vllm_omni/worker/gpu_ar_model_runner.py`

In both cases, the old `else` (non-async-chunk) branch used `partition_payload_list()` which parted out client-facing keys and returned `None` for the inter-stage side. The downstream stage (code2wav) never received any data through the connector, causing the 300-second timeout:

```
[Coordinator stage-1] Request speech-... timed out waiting for chunk/input (waited > 300s)
Marking 1 request(s) as FINISHED_ERROR after waiting > 300s for connector input
```

## Fix

PR [#4792](https://github.com/vllm-project/vllm-omni/pull/4792) corrects the non-async-chunk branch to pass the full payload as both `inter_stage_outputs` and `multimodal_outputs`:

**GPU Generation Runner** (`gpu_generation_model_runner.py:467`):
```python
else:
    # non-async-chunk ships the full payload to the next stage (PR #4792)
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

**GPU AR Runner** (`gpu_ar_model_runner.py:1813`):
```python
else:
    # non-async-chunk ships the full payload to the next stage (PR #4792)
    pooler_inter, pooler_client = pooler_output, pooler_output
```

Equivalent fixes exist for the NPU runners (`npu_generation_model_runner.py:487`, `npu_ar_model_runner.py:1167`).

The PR changes were included in the vLLM 0.24 rebase commit [`a560ed18`](https://github.com/vllm-project/vllm-omni/commit/a560ed184d9197855f1cccf46cb1cac87b0a7138). Your current commit `0899a1a` (vLLM 0.23 / vLLM-Omni 0.20.2) predates that rebase and does not include the fix.

## Workaround

Keep `async_chunk: true` (the default in `vllm_omni/deploy/qwen3_tts.yaml`), which you've already confirmed works:

```bash
curl -s http://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"<served-model>","input":"Hello world","voice":"Vivian","response_format":"wav"}'
```

## Verification

After updating to a commit that includes the fix:

```bash
# 1. Confirm the fix is in your tree
git log --oneline -1  # should show a560ed18 or later
grep -A2 'non-async-chunk ships the full payload' vllm_omni/worker/gpu_generation_model_runner.py

# 2. Run the dedicated regression test
pytest tests/worker/test_gpu_ar_model_runner.py::test_sample_tokens_tail_only_prefix_cache_uses_staged_cpu_hidden_states -xvs

# 3. Serve with async_chunk: false and retry the curl command — should produce audio, not timeout
```

## Prevention

A deploy-config smoke test that exercises `async_chunk: false` for multi-stage pipelines would catch this regression before release. The existing test `test_sample_tokens_tail_only_prefix_cache_uses_staged_cpu_hidden_states` covers the runner-level fix but an end-to-end integration test with a real talker→code2wav pipeline and `async_chunk: false` would close the gap.
