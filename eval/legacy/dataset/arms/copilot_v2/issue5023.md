# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 5023, 'report_only': True, 'post': False, 'params': {}}

## fetch
- **state_updates**: {'issue_text': '{"body":"### Proposal to improve performance\\n\\n_No response_\\n\\n### Report of performance regression\\n\\n## Summary\\n\\nBenchmarked `vllm/vllm-omni:v0.24.0` against `v0.22.0` on Qwen3-TTS (0.6B/1.7B Base + CustomVoice) and Voxtral-4B, H200, TP=1. v0.24.0 is faster single-stream (TTFP ~unchanged at c=1), but **TTFP (time-to-first-packet) regresses 27–41% at concurrency ≥8**.\\n\\n**TTFP is the focus of this report** because it is duration-independent. v0.24.0 also generates ~8.0s mean audio per request vs ~6.2s on v0.22.0 for the same prompts, so the higher end-to-end latency (E2EL) and lower audio-seconds-per-second throughput are largely explained by longer outputs and are **expected, not regressions** — they are included below only as context. TTFP does not depend on output length, and it still degrades sharply under load.\\n\\n## Benchmark setup\\n\\n- **Images:** `vllm/vllm-omni:v0.22.0`, `vllm/vllm-omni:v0.24.0`\\n- **Hardware:** NVIDIA H200, TP=1, `--gpu-memory-utilization 0.45` (two-stage LLM + vocoder pipeline sharing GPU memory)\\n- **Models:** `Qwen/Qwen3-TTS-12Hz-{1.7B,0.6B}-{Base,CustomVoice}`, `mistralai/Voxtral-4B-TTS-2603`\\n- **Bench:** `vllm-omni bench serve --omni --backend openai-audio-speech --endpoint /v1/audio/speech --request-rate inf --num-prompts 100 --max-concurrency {1,4,8,16,25}` — seed-tts / seed-tts-text datasets\\n- **Coverage:** 50 runs total, 0 failures\\n\\n## TTFP regression (Qwen3-TTS-12Hz-1.7B-Base, mean)\\n\\n| c | TTFP (ms) 0.22 → 0.24 | Change |\\n|---|---|---|\\n| 1 | 67 → 66 | ~flat |\\n| 4 | 90 → 99 | +10% |\\n| 8 | 207 → 223 | +7.7% |\\n| 16 | 957 → 1297 | +35.5% |\\n| 25 | 2100 → 2890 | +37.6% |\\n\\n0.6B-Base is worse: **TTFP +41.2% at c=25**.\\n\\n## Context (duration-dependent, expected — not the regression being reported)\\n\\nv0.24.0 emits ~8.0s mean audio/request vs ~6.2s on v0.22.0 for identical prompts (presumably a codec/sampling change). This accounts for the higher E2EL and the audio-seco

## draft
- **status**: success
- **summary**: Investigated the v0.22.0 → v0.24.0 scheduler and model-executor changes for Qwen3-TTS. The TTFP regression at high concurrency is likely caused by increased per-schedule-tick overhead in both the AR (Stage 0) and Generation (Stage 1) schedulers due to newly added scheduling coordination, status-realignment, and connector-output plumbing. The audio-duration change (~6.2s → ~8.0s) appears to be a consequence of changes in the code predictor sampling / stop-token behavior, not a scheduler bug, though it may indirectly amplify TTFP by deepening queues. Specific mitigations are suggested.
- **findings**: ["Pipeline anatomy: Qwen3-TTS is two-stage — Stage 0 (talker, AR scheduler producing codec tokens) → Stage 1 (code2wav, generation scheduler converting codes to audio via OmniGenerationScheduler). TTFP is gated by Stage 0's time to produce the first audio-codec chunk and Stage 1's decode latency.", 'Scheduler overhead growth between v0.22 and v0.24: The unified OmniSchedulerMixin now runs _consume_pending_connector_output(), _process_pending_input_timeouts(), and _realign_request_status_to_queues() on every schedule() tick for both schedulers. Under c≥8 contention, this per-tick bookkeeping adds cumulative delay.', 'OmniSchedulingCoordinator (new in v0.24) parks Stage 1 requests in WAITING_FOR_INPUT until the stage-connector delivers the full codec payload. At high concurrency, the round-trip through the coordinator queue + waiting_for_input deque adds a scheduling delay before the generation scheduler even sees the request.', 'The OmniGenerationScheduler fast-path can fall back to super().schedule() (upstream vLLM scheduler) when KV-cache allocation fails. Under VRAM pressure at --gpu-memory-utilization 0.45 with both stages sharing GPU memory, allocation failures are more likely at high concurrency, triggering the slower fallback path.', "Audio-duration change: The prompt_embeds_builder and talker architecture haven't changed the output-length logic fundamentally. The ~28% increase in audio duration (6.2s→8.0s) likely comes from the code predictor sampling parameters (subtalker_sampling_params with defaults do_sample=True, temperature=0.9, top_k=50) producing codec sequences that take more steps to hit the stop-token (id 2150). This is plausibly intentional or a side effect of upstream model-weight updates.", 'The comment thread contains a collaborator asking to try the latest commit-id, suggesting there may already be post-v0.24 patches that address scheduling efficiency.']
- **files_read**: ['/rebase/vllm-omni/vllm_omni/core/sched/omni_generation_scheduler.py', '/rebase/vllm-omni/vllm_omni/core/sched/omni_ar_scheduler.py', '/rebase/vllm-omni/vllm_omni/core/sched/omni_scheduler_mixin.py', '/rebase/vllm-omni/vllm_omni/core/sched/omni_scheduling_coordinator.py', '/rebase/vllm-omni/vllm_omni/model_executor/models/qwen3_tts/pipeline.py', '/rebase/vllm-omni/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_code2wav.py', '/rebase/vllm-omni/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_talker.py', '/rebase/vllm-omni/vllm_omni/model_executor/models/qwen3_tts/prompt_embeds_builder.py', '/rebase/vllm-omni/vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_code_predictor_vllm.py']
- **files_modified**: []
- **tests_requested**: []
- **tests_run**: []
- **assumptions**: ['The user is running the v0.24.0 release image, not a post-release commit from main.', 'The TTFP metric reported is the time from request arrival to the first audio chunk (not the first token), which for Qwen3-TTS corresponds to Stage 0 producing the first codec row + Stage 1 decode of that row.', "The --gpu-memory-utilization 0.45 flag means both Stage 0 (talker LLM) and Stage 1 (code2wav decoder) share the same GPU memory budget, and the 0.6B/1.7B model sizes leave relatively tight headroom for the code2wav decoder's KV cache and intermediate buffers.", 'The audio-duration change is not caused by a different prompt set or text input; the benchmark uses identical prompts from seed-tts/seed-tts-text datasets.']
- **blockers**: []
- **confidence**: medium
- **failure_kind**: None
- **next_action**: The user should test the latest main-branch commit (as collaborator amy-why-3459 suggested) and, if the regression persists, profile the schedule() tick duration with c≥8 to isolate which subsystem (connector coordination, status realignment, or KV-allocation fallback) is the primary contributor. We can also provide guidance on pinning the old codec-sampling behavior for a clean A/B comparison.
- **answer_draft**: Thank you for the detailed benchmark report — this is really helpful.

## Summary

We've looked through the scheduler and model-executor code that changed between v0.22.0 and v0.24.0 for Qwen3-TTS. The TTFP regression at concurrency ≥ 8 is likely caused by **increased per-schedule-tick overhead** in both the Stage-0 AR scheduler and the Stage-1 generation scheduler, combined with the newly introduced **full-payload input coordinator** for Stage 1. The audio-duration change (~6.2s → ~8.0s) is a separate phenomenon — likely from code predictor sampling behavior — but may indirectly worsen TTFP by keeping requests in the system longer.

## Scheduler changes affecting TTFP

### 1. Per-tick bookkeeping in both schedulers (new in v0.24)

The `OmniSchedulerMixin` (shared by both `OmniARScheduler` and `OmniGenerationScheduler`) now runs these every `schedule()` call:
- `_consume_pending_connector_output()` — drains connector metadata from the previous model-runner step
- `_process_pending_input_timeouts()` — scans for stalled full-payload requests
- `_realign_request_status_to_queues()` — repairs status/queue membership inconsistencies

At c=1 these add negligible overhead, but at c≥8 the cumulative per-tick time grows and delays the scheduling loop. Each tick processes more requests (waiting + running queues both longer), so the O(n) status realignment and timeout scans become measurable.

### 2. Full-payload input coordinator for Stage 1 (new in v0.24)

Stage 1 (code2wav) now uses `OmniSchedulingCoordinator` to park requests in `WAITING_FOR_INPUT` until the stage-connector delivers the complete codec payload from Stage 0. Under high concurrency:
- Requests spend extra scheduling ticks in the coordinator's `_waiting_for_input` deque before being released back to `WAITING`
- The coordinator's `process_pending_full_payload_inputs()` runs on every tick and must scan all waiting requests, adding another O(n) component

### 3. Generation-scheduler fallback path

The `OmniGenera
- **draft_answer**: Thank you for the detailed benchmark report — this is really helpful.

## Summary

We've looked through the scheduler and model-executor code that changed between v0.22.0 and v0.24.0 for Qwen3-TTS. The TTFP regression at concurrency ≥ 8 is likely caused by **increased per-schedule-tick overhead** in both the Stage-0 AR scheduler and the Stage-1 generation scheduler, combined with the newly introduced **full-payload input coordinator** for Stage 1. The audio-duration change (~6.2s → ~8.0s) is a separate phenomenon — likely from code predictor sampling behavior — but may indirectly worsen TTFP by keeping requests in the system longer.

## Scheduler changes affecting TTFP

### 1. Per-tick bookkeeping in both schedulers (new in v0.24)

The `OmniSchedulerMixin` (shared by both `OmniARScheduler` and `OmniGenerationScheduler`) now runs these every `schedule()` call:
- `_consume_pending_connector_output()` — drains connector metadata from the previous model-runner step
- `_process_pending_input_timeouts()` — scans for stalled full-payload requests
- `_realign_request_status_to_queues()` — repairs status/queue membership inconsistencies

At c=1 these add negligible overhead, but at c≥8 the cumulative per-tick time grows and delays the scheduling loop. Each tick processes more requests (waiting + running queues both longer), so the O(n) status realignment and timeout scans become measurable.

### 2. Full-payload input coordinator for Stage 1 (new in v0.24)

Stage 1 (code2wav) now uses `OmniSchedulingCoordinator` to park requests in `WAITING_FOR_INPUT` until the stage-connector delivers the complete codec payload from Stage 0. Under high concurrency:
- Requests spend extra scheduling ticks in the coordinator's `_waiting_for_input` deque before being released back to `WAITING`
- The coordinator's `process_pending_full_payload_inputs()` runs on every tick and must scan all waiting requests, adding another O(n) component

### 3. Generation-scheduler fallback path

The `OmniGenera
- **state_updates**: {'draft_answer': 'Thank you for the detailed benchmark report — this is really helpful.\n\n## Summary\n\nWe\'ve looked through the scheduler and model-executor code that changed between v0.22.0 and v0.24.0 for Qwen3-TTS. The TTFP regression at concurrency ≥ 8 is likely caused by **increased per-schedule-tick overhead** in both the Stage-0 AR scheduler and the Stage-1 generation scheduler, combined with the newly introduced **full-payload input coordinator** for Stage 1. The audio-duration change (~6.2s → ~8.0s) is a separate phenomenon — likely from code predictor sampling behavior — but may indirectly worsen TTFP by keeping requests in the system longer.\n\n## Scheduler changes affecting TTFP\n\n### 1. Per-tick bookkeeping in both schedulers (new in v0.24)\n\nThe `OmniSchedulerMixin` (shared by both `OmniARScheduler` and `OmniGenerationScheduler`) now runs these every `schedule()` call:\n- `_consume_pending_connector_output()` — drains connector metadata from the previous model-runner step\n- `_process_pending_input_timeouts()` — scans for stalled full-payload requests\n- `_realign_request_status_to_queues()` — repairs status/queue membership inconsistencies\n\nAt c=1 these add negligible overhead, but at c≥8 the cumulative per-tick time grows and delays the scheduling loop. Each tick processes more requests (waiting + running queues both longer), so the O(n) status realignment and timeout scans become measurable.\n\n### 2. Full-payload input coordinator for Stage 1 (new in v0.24)\n\nStage 1 (code2wav) now uses `OmniSchedulingCoordinator` to park requests in `WAITING_FOR_INPUT` until the stage-connector delivers the complete codec payload from Stage 0. Under high concurrency:\n- Requests spend extra scheduling ticks in the coordinator\'s `_waiting_for_input` deque before being released back to `WAITING`\n- The coordinator\'s `process_pending_full_payload_inputs()` runs on every tick and must scan all waiting requests, adding another O(n) component\n\n### 3. Generat
