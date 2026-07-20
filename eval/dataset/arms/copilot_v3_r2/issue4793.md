# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
When async_chunk=false, the sample_tokens() methods set inter_stage_outputs=None (or equivalent), starving the downstream stage of data. The downstream stage waited indefinitely for connector input and timed out at 300s. Evidence: vllm_omni/worker/gpu_generation_model_runner.py:464-467 — the else branch comment explicitly states '#4527's (None, per_req_payloads) starved the downstream stage.'

### Fix
Update to a commit that includes the vLLM 0.24 rebase (commit a560ed184d9197855f1cccf46cb1cac87b0a7138 or later on main). The fix changes the non-async-chunk branch from (None, per_req_payloads) to (per_req_payloads, per_req_payloads) so the full payload reaches the downstream stage via inter_stage_outputs.

### Workaround
Use `async_chunk: true` (the default in vllm_omni/deploy/qwen3_tts.yaml) until the rebase is applied.

### Preconditions
The fix requires no special hardware or version constraints beyond what the vLLM 0.24 rebase already requires. The reporter's environment (8× RTX 4090, CUDA 12.2, PyTorch 2.11) is compatible.

### Verification
Serve Qwen3-TTS with `async_chunk: false`, send `curl -s http://localhost:8000/v1/audio/speech -H 'Content-Type: application/json' -d '{"model":"<served-model>","input":"Hello world","voice":"Vivian","response_format":"wav"}'`, confirm audio returns within seconds.

### Prevention
Add a CI integration test that runs a multi-stage TTS pipeline with `async_chunk: false` to catch regressions in this code path. The unit test from PR #4792 (`test_build_omni_output_non_async_chunk_accumulates_full_payload`) should also be preserved in the test suite.

### Disposition
close — fixed by PR #4792 (absorbed into vLLM 0.24 rebase at commit a560ed184). Reopen condition: if the hang reproduces on a checkout that already includes commit a560ed184 or later.

### Additional context
## Root Cause

When `async_chunk: false`, the `sample_tokens()` method in the GPU and NPU model runners was setting `inter_stage_outputs = None` (or equivalent), so the upstream stage never shipped data to the downstream stage via the inter-stage connector. The downstream stage (stage-1, e.g. Code2Wav) waited indefinitely for input from the connector and timed out after 300s.

This was a regression from issue #4527. PR #4792 (<https://github.com/vllm-project/vllm-omni/pull/4792>) fixed it by ensuring the non-async-chunk branch passes the **full payload** to both `inter_stage_outputs` and `multimodal_outputs` instead of `(None, payload)`.

### Evidence (file:line)

All four runner files have the fix in the current `main` (the #4792 diff was absorbed into the vLLM 0.24 rebase at commit `a560ed184`):

- `vllm_omni/worker/gpu_generation_model_runner.py:467` — `inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads`
- `vllm_omni/worker/gpu_ar_model_runner.py:1813` — `pooler_inter, pooler_client = pooler_output, pooler_output`
- `vllm_omni/platforms/npu/worker/npu_generation_model_runner.py:487` — `inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads`
- `vllm_omni/platforms/npu/worker/npu_ar_model_runner.py:1167` — `pooler_inter, pooler_client = pooler_output, pooler_output`

Each location has a comment referencing `#4527` and `PR #4792`.

## Fix

Update your checkout to a commit that includes the vLLM 0.24 rebase (commit `a560ed184d9197855f1cccf46cb1cac87b0a7138` or any later commit on `main`).

Alternatively, cherry-pick the four changed files from that commit:

```bash
git cherry-pick a560ed184d9197855f1cccf46cb1cac87b0a7138 -- \
  vllm_omni/worker/gpu_generation_model_runner.py \
  vllm_omni/worker/gpu_ar_model_runner.py \
  vllm_omni/platforms/npu/worker/npu_generation_model_runner.py \
  vllm_omni/platforms/npu/worker/npu_ar_model_runner.py
```

## Workaround

Use `async_chunk: true` (the default in `vllm_omni/deploy/qwen3_tts.yaml`) until you can update. The default config already works.

## Verification

1. Serve Qwen3-TTS with `async_chunk: false` in the deploy config.
2. Send a request:
   ```bash
   curl -s http://localhost:8000/v1/audio/speech \
     -H 'Content-Type: application/json' \
     -d '{"model":"<served-model>","input":"Hello world","voice":"Vivian","response_format":"wav"}'
   ```
3. Confirm audio is returned within a few seconds (not 300s timeout).

## Prevention

A regression test was added in PR #4792 (`tests/worker/test_gpu_ar_model_runner.py::test_build_omni_output_non_async_chunk_accumulates_full_payload`). Consider adding a similar integration-level CI job that runs a multi-stage TTS pipeline with `async_chunk: false` to catch regressions in this code path.
