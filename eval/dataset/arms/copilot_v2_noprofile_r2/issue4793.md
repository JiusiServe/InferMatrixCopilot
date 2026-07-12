# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root cause

PR #4527 ("separates inter-stage from client outputs") introduced a regression: in the non-`async_chunk` code path of both worker runners, the inter-stage payload was set to `None` instead of the full per-request payload list. This starved the downstream stage.

**Affected files (pre-fix):**

- `vllm_omni/worker/gpu_generation_model_runner.py` — `sample_tokens()` had:
  ```python
  if self._async_chunk:
      inter_stage_outputs, multimodal_outputs = partition_payload_list(per_req_payloads)
  else:
      inter_stage_outputs, multimodal_outputs = None, per_req_payloads   # ← BUG: None skips accumulation
  ```

- `vllm_omni/worker/gpu_ar_model_runner.py` — `_build_omni_model_runner_output_from_snapshot()` had the same pattern:
  ```python
  if self._async_chunk:
      pooler_inter, pooler_client = partition_payload_list(pooler_output)
  else:
      pooler_inter, pooler_client = None, pooler_output   # ← BUG: None skips accumulation
  ```

The `if inter_stage_outputs and self._should_accumulate_full_payload_output():` guard short-circuits on `None`, so `accumulate_full_payload_output()` was never called. Without accumulation, `flush_full_payload_outputs()` is a no-op, and the talker's codec output never reaches the code2wav stage via the shared-memory connector. Stage-1 then waits indefinitely (300s timeout).

## Fix

**PR #4792** ([bugfix] fix audio empty bug for non-async-chunk mode) changes both branches to use the full payload list:

- `gpu_generation_model_runner.py`:
  ```python
  else:
      # See gpu_ar_model_runner: non-async-chunk ships the full payload to the next
      # stage; #4527's (None, per_req_payloads) starved the downstream stage. (PR #4792)
      inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
  ```

- `gpu_ar_model_runner.py`:
  ```python
  else:
      # Non-async-chunk still ships the full payload to the next stage (via
      # accumulate_full_payload_output and the inter_stage_outputs field); only
      # client mm keys are split out when async_chunk is enabled. #4527 set this
      # to (None, pooler_output), which skipped accumulation and starved the
      # downstream stage (300s connector-input timeout / empty audio). (PR #4792)
      pooler_inter, pooler_client = pooler_output, pooler_output
  ```

Same fix applied to the NPU runners (`npu_generation_model_runner.py`, `npu_ar_model_runner.py`).

## Your version

You are on **vLLM 0.23.0 / vllm-omni 0.20.2 (commit `0899a1a`)**. The PR #4792 fix was merged as part of the **vLLM 0.24 rebase** (commit `a560ed184`). Your tree predates the rebase and does **not** include the fix.

## Workaround (available now)

Use `async_chunk: true` — this is the default in `vllm_omni/deploy/qwen3_tts.yaml` and works correctly:

```bash
# In your deploy YAML, keep or set:
async_chunk: true
```

## Verification (after updating)

1. Update to a post-0.24-rebase build:
   ```bash
   git fetch origin
   git checkout origin/main  # or a tag >= 0.24
   pip install -e .
   ```

2. Set `async_chunk: false` in your deploy config and serve:
   ```bash
   vllm-omni serve qwen3_tts --async_chunk false
   ```

3. Send a test request:
   ```bash
   curl -s http://localhost:8000/v1/audio/speech \
     -H 'Content-Type: application/json' \
     -d '{"model":"<served-model>","input":"Hello world","voice":"Vivian","response_format":"wav"}' \
     --max-time 30
   ```

   The request should complete within seconds (not hang).

You can also run the regression test included in PR #4792:
```bash
pytest tests/worker/test_gpu_ar_model_runner.py::test_build_omni_output_non_async_chunk_accumulates_full_payload -xvs
```

## Linked issues / PRs

- **PR #4527** — introduced the regression (separated inter-stage from client outputs)
- **PR #4792** — the fix (merged into the v0.24 rebase)
- **Issue #4793** — this issue

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
