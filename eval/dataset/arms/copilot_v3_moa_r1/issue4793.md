# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
PR #4527 introduced a regression in the non-async-chunk code path of both `gpu_ar_model_runner.py` and `gpu_generation_model_runner.py`, where `inter_stage_outputs` was set to `None` instead of `per_req_payloads`. This caused `accumulate_full_payload_output()` to be skipped, starving the downstream stage of connector input and triggering a 300s timeout. Evidence: `vllm_omni/worker/gpu_generation_model_runner.py:468` and `vllm_omni/worker/gpu_ar_model_runner.py:1816` (current code already shows the corrected line with inline comment referencing PR #4792).

### Fix
In both `vllm_omni/worker/gpu_generation_model_runner.py` (sample_tokens method, non-async-chunk else branch) and `vllm_omni/worker/gpu_ar_model_runner.py` (`_build_omni_model_runner_output_from_snapshot`, non-async-chunk else branch), change `inter_stage_outputs, multimodal_outputs = None, per_req_payloads` to `inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads`. The fix is already on main (PR #4792).

### Workaround
Use the default deploy config with `async_chunk: true` (the default in `vllm_omni/deploy/qwen3_tts.yaml`), which was not affected by this regression. Or upgrade to a vLLM-Omni version that includes the vLLM 0.24 rebase (commit a560ed18 or later).

### Preconditions
The fix requires upgrading to a vLLM-Omni version built from main after commit a560ed18 (the vLLM 0.24 rebase that includes PR #4792). The workaround (async_chunk: true) works on any version.

### Verification
Deploy Qwen3-TTS with a custom config that sets `async_chunk: false` on all stages, send a `/v1/audio/speech` request, and confirm audio is returned within normal latency (no 300s hang). Also run: `pytest tests/worker/test_gpu_ar_model_runner.py::test_build_omni_output_non_async_chunk_accumulates_full_payload -v`

### Prevention
The unit test `test_build_omni_output_non_async_chunk_accumulates_full_payload` (added in PR #4792) guards against regression of the non-async-chunk payload routing. A CI integration test exercising multi-stage TTS with `async_chunk: false` would provide additional coverage.

### Disposition
close — fix is already merged on main via PR #4792 (included in vLLM 0.24 rebase commit a560ed18). Reporter needs to upgrade their version.

### Additional context
Hi, thanks for the report! This is a known regression introduced by PR #4527 and already fixed by **PR [#4792](https://github.com/vllm-project/vllm-omni/pull/4792)**, which has been merged into `main`.

### Root cause

PR #4527 changed the non-async-chunk payload routing in both `gpu_ar_model_runner.py` and `gpu_generation_model_runner.py`. The non-async-chunk branch was accidentally set to:

```python
inter_stage_outputs, multimodal_outputs = None, per_req_payloads
```

Setting `inter_stage_outputs` to `None` meant `accumulate_full_payload_output()` was never called for that request, so the downstream stage (code2wav) never received its connector input — causing the 300s timeout you see in the logs.

### Fix (already on main)

PR #4792 corrected both runners to ship the full payload in both channels:

```python
# gpu_generation_model_runner.py:468
# gpu_ar_model_runner.py:1816
inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

This ensures the downstream stage receives the data it needs via `inter_stage_outputs` → `accumulate_full_payload_output()`.

### How to get the fix

You're on **vLLM-Omni 0.20.2** (commit `0899a1a`) with **vLLM 0.23**. The fix was included in the vLLM 0.24 rebase ([commit a560ed18](https://github.com/vllm-project/vllm-omni/commit/a560ed184d9197855f1cccf46cb1cac87b0a7138)). Please upgrade to a vLLM-Omni release built from `main` (or at least from that commit onwards).

### Workaround (if you can't upgrade yet)

Use the default deploy config which sets `async_chunk: true` — this path was not affected by the regression:

```yaml
# vllm_omni/deploy/qwen3_tts.yaml already defaults to:
async_chunk: true
```

Or explicitly add `async_chunk: true` to each stage in your custom deploy config.
