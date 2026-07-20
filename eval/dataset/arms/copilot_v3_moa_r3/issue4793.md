# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
vllm_omni/worker/gpu_generation_model_runner.py:465-468 — PR #4527 set `inter_stage_outputs=None` in the non-async-chunk path, starving downstream stages of payload data via the connector. The downstream stage (e.g., Qwen3TTSCode2Wav) waits indefinitely for input and times out after 300s.

### Fix
Both `inter_stage_outputs` and `multimodal_outputs` must receive the full `per_req_payloads` list in the non-async-chunk path. Current main already has this: `inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads` at gpu_generation_model_runner.py:468.

### Workaround
Set `async_chunk: true` in your deploy config (this is the default), which avoids the buggy code path entirely.

### Preconditions
vLLM-Omni >= version containing commit a560ed18 (the vLLM 0.24 rebase). The reporter's vLLM-Omni 0.20.2 does NOT contain the fix.

### Verification
Deploy with `async_chunk: false` and verify the /v1/audio/speech endpoint returns audio within seconds instead of hanging for 300s.

### Prevention
The existing unit test `test_build_omni_output_non_async_chunk_accumulates_full_payload` (added by PR #4792) validates this path. Ensure CI covers multi-stage pipelines with `async_chunk: false` in integration/e2e tests.

### Disposition
close — the fix is already merged in main; the reporter just needs to upgrade their vLLM-Omni version

### Additional context
This is a known regression introduced by [PR #4527](https://github.com/vllm-project/vllm-omni/pull/4527) and fixed by [PR #4792](https://github.com/vllm-project/vllm-omni/pull/4792).

## Root cause

In `GPUGenerationModelRunner.sample_tokens()`, PR #4527 changed the non-async-chunk code path to assign:

```python
inter_stage_outputs, multimodal_outputs = None, per_req_payloads
```

This starved the downstream stage (e.g., Qwen3TTSCode2Wav) of input data because `inter_stage_outputs=None` meant the connector coordinator never received a payload to forward. Stage-1 then waited > 300s for connector input and timed out.

The fix (in `vllm_omni/worker/gpu_generation_model_runner.py:465-468`) now correctly ships the full payload to both channels:

```python
if self._async_chunk:
    inter_stage_outputs, multimodal_outputs = partition_payload_list(per_req_payloads)
else:
    # non-async-chunk ships the full payload to the next stage
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

The same fix was applied to the NPU runner (`vllm_omni/platforms/npu/worker/npu_generation_model_runner.py:484-488`).

## Status

The fix is already merged into `main` via the vLLM 0.24 rebase commit ([a560ed18](https://github.com/vllm-project/vllm-omni/commit/a560ed184d9197855f1cccf46cb1cac87b0a7138)). Your reported version (vLLM-Omni 0.20.2, commit `0899a1a`) predates this fix.

## Workaround

1. **Upgrade** to a vLLM-Omni release that includes the 0.24 rebase (>= the commit containing `a560ed18`).
2. **Or** use `async_chunk: true` (the default in `vllm_omni/deploy/qwen3_tts.yaml`), which takes a different code path and is not affected by this regression.

## Verification

After upgrading, re-run your original curl command and confirm audio is returned within a few seconds:

```bash
curl -s http://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"<served-model>","input":"Hello world","voice":"Vivian","response_format":"wav"}' \
  -o output.wav
```

If you still see the hang with `async_chunk: false` on a version that should contain the fix, please report with your exact vLLM-Omni git sha and server logs.
