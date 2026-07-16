# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

Thanks for the clear bug report with logs. The hang in the `async_chunk: false` path is a known regression caused by #4527 and already fixed by PR #4792 — the fix is included in the vLLM 0.24 rebase commit [a560ed184](https://github.com/vllm-project/vllm-omni/commit/a560ed184d9197855f1cccf46cb1cac87b0a7138).

## Root Cause

In the non-async-chunk branch, `sample_tokens()` was setting `inter_stage_outputs = None` instead of forwarding per-request payloads to the downstream connector:

- **`vllm_omni/worker/gpu_generation_model_runner.py:465-468`** — the `else` branch (non-async-chunk) previously returned `(None, per_req_payloads)`, which starved the downstream code2wav stage.
- **`vllm_omni/worker/gpu_ar_model_runner.py:1798-1804`** — same issue on the AR runner side: `pooler_inter` was `None`, skipping full-payload accumulation.

The downstream Stage-1 (code2wav) waits on its connector for input that never arrives, times out after 300s, and marks the request `FINISHED_ERROR` — exactly the log you see.

## The Fix (already on `main`)

PR #4792 (merged) changes both non-async-chunk branches to ship the full payload:

```python
# gpu_generation_model_runner.py (line 468)
inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads

# gpu_ar_model_runner.py (line 1804)
pooler_inter, pooler_client = pooler_output, pooler_output
```

Same fix applied to NPU runners (`npu_generation_model_runner.py:488`, `npu_ar_model_runner.py:1167`).

## Why you're hitting it

Your checkout is on commit `0899a1a` (vLLM-Omni 0.20.2 / vLLM 0.23.0), which predates the vLLM 0.24 rebase that carries the fix.

## Resolution

1. **Rebase or update** to the latest `main` (or any commit at or after `a560ed184`).
2. **Workaround** (if you can't update immediately): use `async_chunk: true` — this is the default in `vllm_omni/deploy/qwen3_tts.yaml` and works correctly.

Let us know if you still see the hang after updating.

## draft_answer

Thanks for the clear bug report with logs. The hang in the `async_chunk: false` path is a known regression caused by #4527 and already fixed by PR #4792 — the fix is included in the vLLM 0.24 rebase commit [a560ed184](https://github.com/vllm-project/vllm-omni/commit/a560ed184d9197855f1cccf46cb1cac87b0a7138).

## Root Cause

In the non-async-chunk branch, `sample_tokens()` was setting `inter_stage_outputs = None` instead of forwarding per-request payloads to the downstream connector:

- **`vllm_omni/worker/gpu_generation_model_runner.py:465-468`** — the `else` branch (non-async-chunk) previously returned `(None, per_req_payloads)`, which starved the downstream code2wav stage.
- **`vllm_omni/worker/gpu_ar_model_runner.py:1798-1804`** — same issue on the AR runner side: `pooler_inter` was `None`, skipping full-payload accumulation.

The downstream Stage-1 (code2wav) waits on its connector for input that never arrives, times out after 300s, and marks the request `FINISHED_ERROR` — exactly the log you see.

## The Fix (already on `main`)

PR #4792 (merged) changes both non-async-chunk branches to ship the full payload:

```python
# gpu_generation_model_runner.py (line 468)
inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads

# gpu_ar_model_runner.py (line 1804)
pooler_inter, pooler_client = pooler_output, pooler_output
```

Same fix applied to NPU runners (`npu_generation_model_runner.py:488`, `npu_ar_model_runner.py:1167`).

## Why you're hitting it

Your checkout is on commit `0899a1a` (vLLM-Omni 0.20.2 / vLLM 0.23.0), which predates the vLLM 0.24 rebase that carries the fix.

## Resolution

1. **Rebase or update** to the latest `main` (or any commit at or after `a560ed184`).
2. **Workaround** (if you can't update immediately): use `async_chunk: true` — this is the default in `vllm_omni/deploy/qwen3_tts.yaml` and works correctly.

Let us know if you still see the hang after updating.

---

## Step diagnostics

### fetch

### draft
- **status**: success
- **summary**: The hang is a known regression introduced by #4527: in the `async_chunk: false` path, both `gpu_ar_model_runner.py` and `gpu_generation_model_runner.py` set `inter_stage_outputs = None` instead of forwarding the full payload, starving the downstream connector stage. The downstream code2wav stage waits 300s for connector input that never arrives, then marks the request as FINISHED_ERROR. PR #4792 fixed this by restoring `inter_stage_outputs = per_req_payloads` (and `pooler_inter = pooler_output`) in the non-async-chunk branch. The fix is already present on main (included in the vLLM 0.24 rebase commit a560ed184d) but the reporter's checkout (commit 0899a1a, vLLM-Omni 0.20.2) predates it.
- **findings**: ['Root cause: gpu_generation_model_runner.py:465-468 — the non-async-chunk branch was setting inter_stage_outputs=None (regression from #4527), which prevented the downstream connector from receiving any payload; the code2wav stage timed out after 300s waiting for input.', 'Root cause: gpu_ar_model_runner.py:1798-1804 — same issue: pooler_inter was None in the non-async-chunk branch, causing the full-payload accumulation path to be skipped.', 'PR #4792 fix (already on main): gpu_generation_model_runner.py:468 — changed to `inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads`.', 'PR #4792 fix (already on main): gpu_ar_model_runner.py:1804 — changed to `pooler_inter, pooler_client = pooler_output, pooler_output`.', 'Same fix also applied to NPU runners: npu_generation_model_runner.py:488 and npu_ar_model_runner.py:1167.', "Reporter is on commit 0899a1a (vLLM-Omni 0.20.2, vLLM 0.23.0) — the fix is in the vLLM 0.24 rebase commit a560ed184d which postdates the reporter's checkout.", 'Workaround: use `async_chunk: true` (the default in `vllm_omni/deploy/qwen3_tts.yaml`) which works correctly.']
- **files_read**: ['/rebase/vllm-omni/vllm_omni/worker/gpu_ar_model_runner.py', '/rebase/vllm-omni/vllm_omni/worker/gpu_generation_model_runner.py', '/rebase/vllm-omni/vllm_omni/platforms/npu/worker/npu_ar_model_runner.py', '/rebase/vllm-omni/vllm_omni/platforms/npu/worker/npu_generation_model_runner.py', '/rebase/vllm-omni/vllm_omni/utils/mm_outputs.py']
- **files_modified**: []
- **tests_requested**: ["pytest tests/worker/test_gpu_ar_model_runner.py -k 'non_async_chunk' -v", 'pytest tests/worker/test_gpu_generation_model_runner.py -v']
- **tests_run**: []
- **assumptions**: ['The reporter is using a Qwen3-TTS deploy config with stages explicitly setting async_chunk: false, bypassing the default in vllm_omni/deploy/qwen3_tts.yaml.', "The reporter's checkout (commit 0899a1a) genuinely lacks the PR #4792 fix, as it predates the vLLM 0.24 rebase.", 'The consumer stage (Qwen3TTSCode2Wav) is properly registered in _FULL_PAYLOAD_INPUT_STAGES for the talker→code2wav connector path.']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: No code changes needed from this agent — the fix (PR #4792) is already on main. The answer should advise the reporter to rebase onto the latest main (or cherry-pick commit a560ed184d) and re-test. If they cannot rebase immediately, the workaround is to use `async_chunk: true`.
- **answer_draft**: Thanks for the clear bug report with logs. The hang in the `async_chunk: false` path is a known regression caused by #4527 and already fixed by PR #4792 — the fix is included in the vLLM 0.24 rebase commit [a560ed184](https://github.com/vllm-project/vllm-omni/commit/a560ed184d9197855f1cccf46cb1cac87b0a7138).

## Root Cause

In the non-async-chunk branch, `sample_tokens()` was setting `inter_stage_outputs = None` instead of forwarding per-request payloads to the downstream connector:

- **`vllm_omni/worker/gpu_generation_model_runner.py:465-468`** — the `else` branch (non-async-chunk) previously returned `(None, per_req_payloads)`, which starved the downstream code2wav stage.
- **`vllm_omni/worker/gpu_ar_model_runner.py:1798-1804`** — same issue on the AR runner side: `pooler_inter` was `None`, skipping full-payload accumulation.

The downstream Stage-1 (code2wav) waits on its connector for input that never arrives, times out after 300s, and marks the request `FINISHED_ERROR` — exactly the log you see.

## The Fix (already on `main`)

PR #4792 (merged) changes both non-async-chunk branches to ship the full payload:

```python
# gpu_generation_model_runner.py (line 468)
inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads

# gpu_ar_model_runner.py (line 1804)
pooler_inter, pooler_client = pooler_output, pooler_output
```

Same fix applied to NPU runners (`npu_generation_model_runner.py:488`, `npu_ar_model_runner.py:1167`).

## Why you're hitting it

Your checkout is on commit `0899a1a` (vLLM-Omni 0.20.2 / vLLM 0.23.0), which predates the vLLM 0.24 rebase that carries the fix.

## Resolution

1. **Rebase or update** to the latest `main` (or any commit at or after `a560ed184`).
2. **Workaround** (if you can't update immediately): use `async_chunk: true` — this is the default in `vllm_omni/deploy/qwen3_tts.yaml` and works correctly.

Let us know if you still see the hang after updating.
