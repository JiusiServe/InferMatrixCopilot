# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

The hang occurs in the `async_chunk=false` (full-payload) path for multi-stage pipelines like Qwen3-TTS (talker → code2wav).

**File & line:** `vllm_omni/worker/gpu_generation_model_runner.py:463-468` and `vllm_omni/worker/gpu_ar_model_runner.py:1808-1815`.

**Mechanism:** In the non-async-chunk branch, a previous change (#4527) set the inter-stage payload to `None`:

```python
# gpu_generation_model_runner.py (broken — #4527):
else:
    inter_stage_outputs, multimodal_outputs = None, per_req_payloads
```

This starves `accumulate_full_payload_output`, so when the talker (Stage-0) finishes, `flush_full_payload_outputs` has nothing to send to the downstream code2wav stage. Meanwhile, Stage-1's `OmniSchedulingCoordinator` (in `omni_scheduling_coordinator.py`) parks requests in `WAITING_FOR_INPUT`, expecting a full-payload delivery on the worker connector. That delivery never arrives because the accumulator was never fed, so the request times out after 300s.

The scheduling gate lives in `_FULL_PAYLOAD_INPUT_STAGES` which includes `('Qwen3TTSCode2Wav', 'code2wav')` — only triggered when `async_chunk=False`.

## Fix

PR #4792 restores the correct routing:

```python
# gpu_generation_model_runner.py (fixed — PR #4792):
else:
    # See gpu_ar_model_runner: non-async-chunk ships the full payload to the next
    # stage; #4527's (None, per_req_payloads) starved the downstream stage. (PR #4792)
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

And in `gpu_ar_model_runner.py`:

```python
else:
    pooler_inter, pooler_client = pooler_output, pooler_output
```

This PR was merged as part of the vLLM 0.24 rebase (commit `a560ed184d9197855f1cccf46cb1cac87b0a7138`).

## Workaround

Until you can pick up the fix, use `async_chunk: true` (the default in `vllm_omni/deploy/qwen3_tts.yaml`) — it is not affected by this bug.

## Verification

1. Rebase to `a560ed18` (or later) or cherry-pick the changes from PR #4792.
2. Set `async_chunk: false` in your deploy config.
3. Run the same `curl /v1/audio/speech` command — it should return audio immediately instead of timing out.
4. The existing unit test `test_build_omni_output_non_async_chunk_accumulates_full_payload` in `tests/worker/test_gpu_ar_model_runner.py` covers this path.

## Linked

- **Fix PR:** #4792
- **Regression:** #4527

## draft_answer

## Root Cause

The hang occurs in the `async_chunk=false` (full-payload) path for multi-stage pipelines like Qwen3-TTS (talker → code2wav).

**File & line:** `vllm_omni/worker/gpu_generation_model_runner.py:463-468` and `vllm_omni/worker/gpu_ar_model_runner.py:1808-1815`.

**Mechanism:** In the non-async-chunk branch, a previous change (#4527) set the inter-stage payload to `None`:

```python
# gpu_generation_model_runner.py (broken — #4527):
else:
    inter_stage_outputs, multimodal_outputs = None, per_req_payloads
```

This starves `accumulate_full_payload_output`, so when the talker (Stage-0) finishes, `flush_full_payload_outputs` has nothing to send to the downstream code2wav stage. Meanwhile, Stage-1's `OmniSchedulingCoordinator` (in `omni_scheduling_coordinator.py`) parks requests in `WAITING_FOR_INPUT`, expecting a full-payload delivery on the worker connector. That delivery never arrives because the accumulator was never fed, so the request times out after 300s.

The scheduling gate lives in `_FULL_PAYLOAD_INPUT_STAGES` which includes `('Qwen3TTSCode2Wav', 'code2wav')` — only triggered when `async_chunk=False`.

## Fix

PR #4792 restores the correct routing:

```python
# gpu_generation_model_runner.py (fixed — PR #4792):
else:
    # See gpu_ar_model_runner: non-async-chunk ships the full payload to the next
    # stage; #4527's (None, per_req_payloads) starved the downstream stage. (PR #4792)
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

And in `gpu_ar_model_runner.py`:

```python
else:
    pooler_inter, pooler_client = pooler_output, pooler_output
```

This PR was merged as part of the vLLM 0.24 rebase (commit `a560ed184d9197855f1cccf46cb1cac87b0a7138`).

## Workaround

Until you can pick up the fix, use `async_chunk: true` (the default in `vllm_omni/deploy/qwen3_tts.yaml`) — it is not affected by this bug.

## Verification

1. Rebase to `a560ed18` (or later) or cherry-pick the changes from PR #4792.
2. Set `async_chunk: false` in your deploy config.
3. Run the same `curl /v1/audio/speech` command — it should return audio immediately instead of timing out.
4. The existing unit test `test_build_omni_output_non_async_chunk_accumulates_full_payload` in `tests/worker/test_gpu_ar_model_runner.py` covers this path.

## Linked

- **Fix PR:** #4792
- **Regression:** #4527

---

## Step diagnostics

### fetch

### draft
- **status**: success
- **summary**: The `async_chunk: false` hang is caused by a missing inter-stage payload routing fix from PR #4792. In the non-async-chunk branch of both `gpu_generation_model_runner.py` and `gpu_ar_model_runner.py`, the inter-stage payload was set to `None` (regression #4527), so `accumulate_full_payload_output` never received data, and `flush_full_payload_outputs` had nothing to send. Stage-1's `OmniSchedulingCoordinator` parks requests in `WAITING_FOR_INPUT` expecting a full-payload delivery that never arrives, causing the 300s timeout. PR #4792 restores the correct routing by shipping the full payload through `inter_stage_outputs` in both runner variants; it was merged as part of the vLLM 0.24 rebase commit (a560ed18). The user's commit 0899a1a (vllm 0.23) predates that rebase and does not include the fix.
- **findings**: ['Root cause: lines 463-468 of gpu_generation_model_runner.py and lines 1808-1815 of gpu_ar_model_runner.py — in the `else` (non-async-chunk) branch, #4527 set `inter_stage_outputs` / `pooler_inter` to `None` instead of `per_req_payloads` / `pooler_output`, starving the downstream accumulator.', "Downstream mechanism: `OmniSchedulingCoordinator` (in omni_scheduling_coordinator.py) gates Stage-1 with `uses_full_payload_input_coordinator()` → `_FULL_PAYLOAD_INPUT_STAGES` includes `('Qwen3TTSCode2Wav','code2wav')`. When `async_chunk=False`, requests are parked in `WAITING_FOR_INPUT` until the worker connector's background recv thread delivers the full payload.", 'The fix: PR #4792 changed the non-async-chunk branch to `inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads` (gen runner) and `pooler_inter, pooler_client = pooler_output, pooler_output` (AR runner).', 'The PR #4792 fix was included in the vLLM 0.24 rebase commit a560ed184d9197855f1cccf46cb1cac87b0a7138.', 'User is on commit 0899a1a (vllm 0.23 / vllm-omni 0.20.2), which predates the 0.24 rebase and does not include the fix.']
- **files_read**: ['/rebase/vllm-omni/vllm_omni/worker/gpu_generation_model_runner.py', '/rebase/vllm-omni/vllm_omni/worker/gpu_ar_model_runner.py', '/rebase/vllm-omni/vllm_omni/core/sched/omni_scheduling_coordinator.py', '/rebase/vllm-omni/vllm_omni/worker/omni_connector_model_runner_mixin.py', '/rebase/vllm-omni/vllm_omni/core/sched/omni_ar_scheduler.py', '/rebase/vllm-omni/vllm_omni/engine/orchestrator.py', '/rebase/vllm-omni/vllm_omni/deploy/qwen3_tts.yaml']
- **files_modified**: []
- **tests_requested**: ['pytest tests/worker/test_gpu_ar_model_runner.py::test_build_omni_output_non_async_chunk_accumulates_full_payload', 'Manual smoke: serve qwen3_tts.yaml with async_chunk: false and curl /v1/audio/speech']
- **tests_run**: []
- **assumptions**: ["User's commit 0899a1a predates the v0.24 rebase that includes PR #4792 — confirmed by vllm 0.23 vs the rebase being tagged 0.24.", 'The non-async-chunk full-payload flow relies on the same accumulate/flush/send pipeline as documented in omni_connector_model_runner_mixin.py.', 'The Qwen3TTSCode2Wav entry in _FULL_PAYLOAD_INPUT_STAGES means Stage-1 will use WAITING_FOR_INPUT coordination.']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: Advise user to rebase onto a vllm-omni checkout that includes commit a560ed18 (the v0.24 rebase) OR apply PR #4792 patch manually. Merge is blocked on rebase: if user cannot rebase immediately, workaround is `async_chunk: true` (the default).
- **answer_draft**: ## Root Cause

The hang occurs in the `async_chunk=false` (full-payload) path for multi-stage pipelines like Qwen3-TTS (talker → code2wav).

**File & line:** `vllm_omni/worker/gpu_generation_model_runner.py:463-468` and `vllm_omni/worker/gpu_ar_model_runner.py:1808-1815`.

**Mechanism:** In the non-async-chunk branch, a previous change (#4527) set the inter-stage payload to `None`:

```python
# gpu_generation_model_runner.py (broken — #4527):
else:
    inter_stage_outputs, multimodal_outputs = None, per_req_payloads
```

This starves `accumulate_full_payload_output`, so when the talker (Stage-0) finishes, `flush_full_payload_outputs` has nothing to send to the downstream code2wav stage. Meanwhile, Stage-1's `OmniSchedulingCoordinator` (in `omni_scheduling_coordinator.py`) parks requests in `WAITING_FOR_INPUT`, expecting a full-payload delivery on the worker connector. That delivery never arrives because the accumulator was never fed, so the request times out after 300s.

The scheduling gate lives in `_FULL_PAYLOAD_INPUT_STAGES` which includes `('Qwen3TTSCode2Wav', 'code2wav')` — only triggered when `async_chunk=False`.

## Fix

PR #4792 restores the correct routing:

```python
# gpu_generation_model_runner.py (fixed — PR #4792):
else:
    # See gpu_ar_model_runner: non-async-chunk ships the full payload to the next
    # stage; #4527's (None, per_req_payloads) starved the downstream stage. (PR #4792)
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

And in `gpu_ar_model_runner.py`:

```python
else:
    pooler_inter, pooler_client = pooler_output, pooler_output
```

This PR was merged as part of the vLLM 0.24 rebase (commit `a560ed184d9197855f1cccf46cb1cac87b0a7138`).

## Workaround

Until you can pick up the fix, use `async_chunk: true` (the default in `vllm_omni/deploy/qwen3_tts.yaml`) — it is not affected by this bug.

## Verification

1. Rebase to `a560ed18` (or later) or cherry-pick the changes from PR #4792.
2. Set `async_chu
