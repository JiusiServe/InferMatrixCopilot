# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root cause

This is the same bug as #4527, fixed by **PR #4792** ("fix audio empty bug for non-async-chunk mode"). When `async_chunk: false`, the non-async-chunk path in both model runners was assigning `inter_stage_outputs = None` to the connector accumulator — the downstream Stage-1 code2wav never received the full payload, so the coordinator timed out waiting for input.

The decisive lines (current main):

**`vllm_omni/worker/gpu_generation_model_runner.py:464-468`** (code2wav runner):
```python
if self._async_chunk:
    inter_stage_outputs, multimodal_outputs = partition_payload_list(per_req_payloads)
else:
    # See gpu_ar_model_runner: non-async-chunk ships the full payload to the next
    # stage; #4527's (None, per_req_payloads) starved the downstream stage. (PR #4792)
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

**`vllm_omni/worker/gpu_ar_model_runner.py`** (talker runner, in `_build_omni_model_runner_output_from_snapshot`, ~line 1812-1815): same pattern — before PR #4792 this was `(None, pooler_output)`, now `(pooler_output, pooler_output)`.

## Mechanism

1. You set `async_chunk: false` in your stages → the connector switches from streaming-chunk mode to full-payload mode.
2. Stage-0 (talker) finishes generating codec frames. Its `sample_tokens` calls `_should_accumulate_full_payload_output()` → True (pipeline config wires `custom_process_next_stage_input_func=talker2code2wav_full_payload`), so it accumulates per-step payloads and flushes them via `SharedMemoryConnector.put()` when the request finishes.
3. Stage-1 (code2wav) is parked in `WAITING_FOR_INPUT` by `OmniSchedulingCoordinator` (gate: `uses_full_payload_input_coordinator` at `vllm_omni/core/sched/omni_scheduling_coordinator.py:51`, entry `("Qwen3TTSCode2Wav", "code2wav")`).
4. **Before PR #4792**: the accumulator received `None` for `inter_stage_outputs`, so `_pending_full_payload_send` was never populated → `flush_full_payload_outputs` had nothing to send → Stage-1 timed out.
5. **After PR #4792**: `inter_stage_outputs = per_req_payloads` → accumulator is fed → flush sends the full codec payload → Stage-1 receives it and runs.

## Your checkout

Your `collect_env.py` reports vLLM-Omni **0.20.2** (commit `0899a1a`). The PR #4792 fix was cherry-picked into the **v0.24 rebase** (commit `a560ed1`). You simply need to update to current `main`.

## Workaround (if you can't update immediately)

Use the default `async_chunk: true` (which is what `vllm_omni/deploy/qwen3_tts.yaml` ships). The chunk-streaming path is the production-tested code path for Qwen3-TTS.

## Verification

After updating to latest main:
```bash
curl -s http://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"<served-model>","input":"Hello world","voice":"Vivian","response_format":"wav"}' \
  --max-time 60 -o /tmp/test.wav
# Should return audio within a few seconds; check file size:
ls -la /tmp/test.wav
```

The unit test `tests/worker/test_gpu_ar_model_runner.py::test_sample_tokens_tail_only_prefix_cache_uses_staged_cpu_hidden_states` also explicitly validates this fix.

## Linked issues/PRs

- **PR #4792** — the fix (merged/closed, changes confirmed present on current main)
- **Issue #4527** — original report of the `(None, per_req_payloads)` starvation

Thanks @amy-why-3459 for pointing to PR #4792 — that's exactly the right fix. @akshatvishu is correct that the fix is already in the v0.24 rebase commit; your checkout just needs to be updated to pick it up.
