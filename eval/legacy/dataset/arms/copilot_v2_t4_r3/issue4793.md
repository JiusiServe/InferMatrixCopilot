# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

The bug was introduced by PR #4527, which changed the non-`async_chunk` code path in `sample_tokens()` to ship `inter_stage_outputs = None` (generation runner) or `pooler_inter = None` (AR runner). Because `accumulate_full_payload_output()` is gated on `inter_stage_outputs` / `pooler_inter` being truthy, **no data was ever accumulated or flushed to the connector**. The downstream stage (code2wav) then waited indefinitely for connector input, hitting the 300s timeout exactly as shown in your log:

```
[Coordinator stage-1] Request speech-... timed out waiting for chunk/input (waited > 300s)
```

### Specific code locations (current main, post-fix):

- **`vllm_omni/worker/gpu_ar_model_runner.py:1808-1814`** (AR/talker producer):
  ```python
  if self._async_chunk:
      pooler_inter, pooler_client = partition_payload_list(pooler_output)
  else:
      # Non-async-chunk still ships the full payload to the next stage; 
      # #4527's (None, pooler_output) starved the downstream stage. (PR #4792)
      pooler_inter, pooler_client = pooler_output, pooler_output
  ```

- **`vllm_omni/worker/gpu_generation_model_runner.py:463-467`** (generation/consumer side):
  ```python
  if self._async_chunk:
      inter_stage_outputs, multimodal_outputs = partition_payload_list(per_req_payloads)
  else:
      # #4527's (None, per_req_payloads) starved the downstream stage. (PR #4792)
      inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
  ```

Identical fixes are in the NPU runners (`npu_ar_model_runner.py`, `npu_generation_model_runner.py`).

## Fix Status

PR #4792 ([bugfix] fix audio empty bug for non-async-chunk mode) contains the correct fix. It was closed as conflicting and never directly merged, but **its code changes were cherry-picked into the vLLM 0.24 rebase commit** (`a560ed184`). The current main branch has the fix in all four runner files.

Your version (vLLM-Omni 0.20.2, commit `0899a1a`) predates this fix.

## Workaround (today)

Use `async_chunk: true` (the default in `vllm_omni/deploy/qwen3_tts.yaml`), which works correctly and is the recommended path for Qwen3-TTS.

## Fix (permanent)

Update to a branch that includes the vLLM 0.24 rebase (commit `a560ed184` or later).

Alternatively, cherry-pick the one-line fix into your current checkout. In both `gpu_ar_model_runner.py` and `gpu_generation_model_runner.py`, find the `else:` branch under `if self._async_chunk:` in `sample_tokens()` (or `_build_omni_model_runner_output_from_snapshot()`) and change the tuple from `(None, payload)` to `(payload, payload)`.

## Verification

After applying the fix, run your `async_chunk: false` deploy config again:
```bash
curl -s http://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"<served-model>","input":"Hello world","voice":"Vivian","response_format":"wav"}'
```
You should receive valid audio rather than a hang/300s timeout.

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (

(promote with SkillStore.promote(name); candidates are never auto-activated)
