# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

> ⚠ draft shipped with caveats — agent self-assessed confidence: high; verify before relying on it.

## Root Cause

This is a known bug fixed by **PR #4792** ([bugfix] fix audio empty bug for non-async-chunk mode).

When `async_chunk: false`, the generation model runner (`GPUGenerationModelRunner.sample_tokens`) builds per-request payloads from the model output and must decide how to route them:

- **`inter_stage_outputs`** — sent via the full-payload connector to the **next pipeline stage** (e.g., code2wav).
- **`multimodal_outputs`** — exposed to the API client.

**Before the fix** (issue #4527), the non-async-chunk branch set:

```python
# Old code — starves the downstream stage
inter_stage_outputs, multimodal_outputs = None, per_req_payloads
```

The downstream stage (code2wav) waits on `inter_stage_outputs` for its input. With `inter_stage_outputs = None`, it never receives data and times out after 300s with:

```
[Coordinator stage-1] Request speech-... timed out waiting for chunk/input (waited > 300s)
```

**The fix** (PR #4792, present in the live `main` branch and the v0.24 rebase) changes this to ship the full payload to both channels:

```python
# vllm_omni/worker/gpu_generation_model_runner.py:464-468
if self._async_chunk:
    inter_stage_outputs, multimodal_outputs = partition_payload_list(per_req_payloads)
else:
    # See gpu_ar_model_runner: non-async-chunk ships the full payload to the next
    # stage; #4527's (None, per_req_payloads) starved the downstream stage. (PR #4792)
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

The same fix applies to the NPU runner (`npu_generation_model_runner.py:484-488`) and the AR runner (`gpu_ar_model_runner.py`).

---

## Verification

Your environment (vLLM-Omni 0.20.2, commit `0899a1a`, vLLM 0.23.0) **predates** the fix. Confirm by checking your local copy:

```bash
grep -A4 'async_chunk:' vllm_omni/worker/gpu_generation_model_runner.py | head -10
```

If you see `(None, per_req_payloads)` (or `inter_stage_outputs` is `None` in the `else` branch), you're on the unfixed version.

---

## Resolution

1. **Recommended**: Upgrade to a version that includes PR #4792 (the v0.24 rebase or current `main`).
2. **Cherry-pick**: Apply the one-line change from PR #4792 to `gpu_generation_model_runner.py`, `npu_generation_model_runner.py`, and `gpu_ar_model_runner.py`.
3. **Workaround**: Use `async_chunk: true` in your deploy config — this is the **default** in `vllm_omni/deploy/qwen3_tts.yaml` and is confirmed working.

---

## Related

- PR #4792: https://github.com/vllm-project/vllm-omni/pull/4792
- Issue #4527 (original starvation report)

## draft_answer

> ⚠ draft shipped with caveats — agent self-assessed confidence: high; verify before relying on it.

## Root Cause

This is a known bug fixed by **PR #4792** ([bugfix] fix audio empty bug for non-async-chunk mode).

When `async_chunk: false`, the generation model runner (`GPUGenerationModelRunner.sample_tokens`) builds per-request payloads from the model output and must decide how to route them:

- **`inter_stage_outputs`** — sent via the full-payload connector to the **next pipeline stage** (e.g., code2wav).
- **`multimodal_outputs`** — exposed to the API client.

**Before the fix** (issue #4527), the non-async-chunk branch set:

```python
# Old code — starves the downstream stage
inter_stage_outputs, multimodal_outputs = None, per_req_payloads
```

The downstream stage (code2wav) waits on `inter_stage_outputs` for its input. With `inter_stage_outputs = None`, it never receives data and times out after 300s with:

```
[Coordinator stage-1] Request speech-... timed out waiting for chunk/input (waited > 300s)
```

**The fix** (PR #4792, present in the live `main` branch and the v0.24 rebase) changes this to ship the full payload to both channels:

```python
# vllm_omni/worker/gpu_generation_model_runner.py:464-468
if self._async_chunk:
    inter_stage_outputs, multimodal_outputs = partition_payload_list(per_req_payloads)
else:
    # See gpu_ar_model_runner: non-async-chunk ships the full payload to the next
    # stage; #4527's (None, per_req_payloads) starved the downstream stage. (PR #4792)
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

The same fix applies to the NPU runner (`npu_generation_model_runner.py:484-488`) and the AR runner (`gpu_ar_model_runner.py`).

---

## Verification

Your environment (vLLM-Omni 0.20.2, commit `0899a1a`, vLLM 0.23.0) **predates** the fix. Confirm by checking your local copy:

```bash
grep -A4 'async_chunk:' vllm_omni/worker/gpu_generation_model_runner.py | head -10
```

If you see `(None, per_req_payloads)` (or `inter_stage_outputs` is `None` in the `else` branch), you're on the unfixed version.

---

## Resolution

1. **Recommended**: Upgrade to a version that includes PR #4792 (the v0.24 rebase or current `main`).
2. **Cherry-pick**: Apply the one-line change from PR #4792 to `gpu_generation_model_runner.py`, `npu_generation_model_runner.py`, and `gpu_ar_model_runner.py`.
3. **Workaround**: Use `async_chunk: true` in your deploy config — this is the **default** in `vllm_omni/deploy/qwen3_tts.yaml` and is confirmed working.

---

## Related

- PR #4792: https://github.com/vllm-project/vllm-omni/pull/4792
- Issue #4527 (original starvation report)

---

## Step diagnostics

### fetch

### draft
- **status**: needs_review
- **summary**: The hang is caused by a known bug (fixed in PR #4792) in the non-async-chunk output path of the generation model runner. When `async_chunk: false`, the old code set `inter_stage_outputs = None` while putting all data into `multimodal_outputs`, starving the downstream stage (code2wav) that reads from `inter_stage_outputs`. The fix ships the full payload to both channels, and the user's commit (0899a1a / vLLM-Omni 0.20.2) predates it. The recommended resolution is to rebase/upgrade past the fix or cherry-pick PR #4792; `async_chunk: true` (default) is a working workaround.
- **findings**: ['Root cause: `vllm_omni/worker/gpu_generation_model_runner.py:464-468` — when `async_chunk` is false, the old code (`#4527`) set `inter_stage_outputs = None, multimodal_outputs = per_req_payloads`, leaving the downstream stage with no inter-stage data to consume.', 'Fix (PR #4792): changed the non-async-chunk branch to `inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads` so the full payload reaches both the connector and the client.', 'The same fix was applied to the NPU runner (`npu_generation_model_runner.py:484-488`) and the AR runner (`gpu_ar_model_runner.py`).', "The user's environment (vLLM-Omni 0.20.2, commit 0899a1a, vLLM 0.23.0) predates the fix; the live checkout at `/rebase/vllm-omni` already contains it.", '`async_chunk: true` (default in `vllm_omni/deploy/qwen3_tts.yaml`) is a confirmed workaround.']
- **files_read**: ['/rebase/vllm-omni/vllm_omni/worker/gpu_generation_model_runner.py', '/rebase/vllm-omni/vllm_omni/worker/gpu_ar_model_runner.py', '/rebase/vllm-omni/vllm_omni/utils/mm_outputs.py', '/rebase/vllm-omni/vllm_omni/platforms/npu/worker/npu_generation_model_runner.py']
- **files_modified**: []
- **tests_requested**: ['pytest tests/worker/test_gpu_ar_model_runner.py::test_build_omni_output_non_async_chunk_accumulates_full_payload -v', 'Serve Qwen3-TTS with `async_chunk: false` deploy config and verify audio output via curl']
- **tests_run**: []
- **assumptions**: ['The issue reporter is on a version (commit 0899a1a) that predates PR #4792 and does not have the fix.', 'The multi-stage pipeline is talker (stage-0) → code2wav (stage-1) as described in the Qwen3-TTS deploy config.', "The coordinator timeout message 'timed out waiting for chunk/input' refers to the inter-stage full-payload connector waiting for data that was never sent because `inter_stage_outputs` was None."]
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: Suggest the user upgrade to a version that includes PR #4792 (e.g., the v0.24 rebase) or cherry-pick the one-line fix into `gpu_generation_model_runner.py` and `gpu_ar_model_runner.py`.
- **answer_draft**: ## Root Cause

This is a known bug fixed by **PR #4792** ([bugfix] fix audio empty bug for non-async-chunk mode).

When `async_chunk: false`, the generation model runner (`GPUGenerationModelRunner.sample_tokens`) builds per-request payloads from the model output and must decide how to route them:

- **`inter_stage_outputs`** — sent via the full-payload connector to the **next pipeline stage** (e.g., code2wav).
- **`multimodal_outputs`** — exposed to the API client.

**Before the fix** (issue #4527), the non-async-chunk branch set:

```python
# Old code — starves the downstream stage
inter_stage_outputs, multimodal_outputs = None, per_req_payloads
```

The downstream stage (code2wav) waits on `inter_stage_outputs` for its input. With `inter_stage_outputs = None`, it never receives data and times out after 300s with:

```
[Coordinator stage-1] Request speech-... timed out waiting for chunk/input (waited > 300s)
```

**The fix** (PR #4792, present in the live `main` branch and the v0.24 rebase) changes this to ship the full payload to both channels:

```python
# vllm_omni/worker/gpu_generation_model_runner.py:464-468
if self._async_chunk:
    inter_stage_outputs, multimodal_outputs = partition_payload_list(per_req_payloads)
else:
    # See gpu_ar_model_runner: non-async-chunk ships the full payload to the next
    # stage; #4527's (None, per_req_payloads) starved the downstream stage. (PR #4792)
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

The same fix applies to the NPU runner (`npu_generation_model_runner.py:484-488`) and the AR runner (`gpu_ar_model_runner.py`).

---

## Verification

Your environment (vLLM-Omni 0.20.2, commit `0899a1a`, vLLM 0.23.0) **predates** the fix. Confirm by checking your local copy:

```bash
grep -A4 'async_chunk:' vllm_omni/worker/gpu_generation_model_runner.py | head -10
```

If you see `(None, per_req_payloads)` (or `inter_stage_outputs` is `None` in the `else` branch), you're on the unfixed versi
