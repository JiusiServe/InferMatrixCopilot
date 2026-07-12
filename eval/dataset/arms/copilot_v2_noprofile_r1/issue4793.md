# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root cause

This is a confirmed regression from PR #4527 affecting multi-stage pipelines with `async_chunk: false`. The bug lives in two files:

**`vllm_omni/worker/gpu_ar_model_runner.py` ~line 1812** and **`vllm_omni/worker/gpu_generation_model_runner.py` ~line 464**.

The non-async-chunk branch was:

```python
# gpu_ar_model_runner.py (old, broken)
if self._async_chunk:
    pooler_inter, pooler_client = partition_payload_list(pooler_output)
else:
    pooler_inter, pooler_client = None, pooler_output   # ← BUG
```

```python
# gpu_generation_model_runner.py (old, broken)
if self._async_chunk:
    inter_stage_outputs, multimodal_outputs = partition_payload_list(per_req_payloads)
else:
    inter_stage_outputs, multimodal_outputs = None, per_req_payloads   # ← BUG
```

Setting `inter_stage_outputs`/`pooler_inter` to `None` skips `accumulate_full_payload_output()`, so the inter-stage connector never gets the payload. The downstream stage's coordinator (`omni_scheduling_coordinator.py`) parks requests in `WAITING_FOR_INPUT` and they eventually time out at 300s — exactly the log line you see:

```
[Coordinator stage-1] Request speech-... timed out waiting for chunk/input (waited > 300s)
```

## Fix

PR #4792 ("[bugfix] fix audio empty bug for non-async-chunk mode") corrects both runners to ship the full payload on the non-async-chunk path:

```python
# Fixed (current main)
else:
    # See gpu_ar_model_runner: non-async-chunk ships the full payload to the next
    # stage; #4527's (None, per_req_payloads) starved the downstream stage. (PR #4792)
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

The fix was incorporated in the vLLM 0.24 rebase (commit `a560ed184d9197855f1cccf46cb1cac87b0a7138`). Your commit `0899a1a` (vllm-omni 0.20.2) predates that rebase.

## Workaround (immediate)

Use `async_chunk: true` in your deploy config — that is the default in `vllm_omni/deploy/qwen3_tts.yaml` and it works correctly:

```yaml
# deploy config top-level
async_chunk: true
```

## Verification

1. Update to a revision that includes the rebase (e.g. `git pull` on main).
2. Serve with your `async_chunk: false` deploy config and run:
   ```bash
   curl -s http://localhost:8000/v1/audio/speech \
     -H 'Content-Type: application/json' \
     -d '{"model":"<served-model>","input":"Hello world","voice":"Vivian","response_format":"wav"}'
   ```
3. You should get a valid WAV response instead of a hang/timeout.

The fix is also covered by the test `tests/worker/test_gpu_ar_model_runner.py::test_build_omni_output_non_async_chunk_accumulates_full_payload`.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
