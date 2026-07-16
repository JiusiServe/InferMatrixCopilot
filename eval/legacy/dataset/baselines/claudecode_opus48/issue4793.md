I have everything I need. Here is my maintainer answer.

---

## Answer to issue #4793 — `async_chunk: false` multi-stage pipelines hang

**This is a real, already-diagnosed-and-fixed regression, not a config error on your side.** The fix is **PR #4792**, which is merged. As @amy-why-3459 and @akshatvishu already noted, it's also folded into the vLLM `0.24` rebase commit `a560ed18`. Closing as fixed is correct — you just need code that post-dates the fix. Your report is on vllm-omni `0.20.2` (commit `0899a1a`), which predates it.

### Root cause

For Qwen3-TTS the pipeline is Stage 0 `Qwen3TTSTalker` → Stage 1 `Qwen3TTSCode2Wav`, and Stage 1 is registered as a **full-payload consumer**:

- `vllm_omni/core/sched/omni_scheduling_coordinator.py:51` — `("Qwen3TTSCode2Wav", "code2wav")` in `_FULL_PAYLOAD_INPUT_STAGES`.

Because Stage 1 is in that set, the coordinator **parks** the Stage-1 request in `WAITING_FOR_INPUT` until the talker's worker connector actually delivers the payload. The only thing that produces that delivery on the talker side is `accumulate_full_payload_output(...)`, and that call is gated on the producer's inter-stage list being non-empty:

- `vllm_omni/worker/gpu_ar_model_runner.py:1818` — `if pooler_inter and self._should_accumulate_full_payload_output(): ... accumulate_full_payload_output(...)`

The regression came from **#4527**, which in the non-async-chunk branch set the split to `(None, pooler_output)`. With the inter-stage element `None`, `pooler_inter` is falsy → `accumulate_full_payload_output` is **skipped** → nothing is ever shipped over the worker connector → Stage 1 waits forever, then the coordinator/scheduler kill it:

- `vllm_omni/core/sched/omni_scheduling_coordinator.py:308` — `"[Coordinator stage-%s] Request %s timed out waiting for chunk/input (waited > %.0fs)"`
- `vllm_omni/core/sched/omni_scheduler_mixin.py:106` — `"Marking %d request(s) as FINISHED_ERROR after waiting > %.0fs for connector input"`

That matches your log exactly (`stage-1 ... timed out waiting for chunk/input`, then `FINISHED_ERROR`, empty audio). The `async_chunk: true` path never hit this because it splits via `partition_payload_list(...)` (`vllm_omni/utils/mm_outputs.py:47`), which keeps the inter-stage keys populated — hence only the `async_chunk=false` path regressed.

### The fix (PR #4792)

The non-async-chunk branch must ship the **full** payload to the next stage (both the inter-stage channel *and* the client channel), so accumulation runs and the consumer is released. This is what's now in the tree:

- `vllm_omni/worker/gpu_ar_model_runner.py:1808-1816`
  ```python
  if self._async_chunk:
      pooler_inter, pooler_client = partition_payload_list(pooler_output)
  else:
      # Non-async-chunk still ships the full payload to the next stage ...
      # #4527 set this to (None, pooler_output), which skipped accumulation
      # and starved the downstream stage (300s connector-input timeout). (PR #4792)
      pooler_inter, pooler_client = pooler_output, pooler_output
  ```
- The same one-liner is mirrored in the diffusion/generation runner at `vllm_omni/worker/gpu_generation_model_runner.py:463-468` (`inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads`).

### What to do

1. **Recommended:** upgrade to any build that contains PR #4792 (e.g. the `0.24` rebase at `a560ed18` or newer). Your hang goes away with no config change; you can keep `async_chunk: false`.
2. **If you can't upgrade yet:** cherry-pick #4792 — it's the two small `else`-branch edits above in `gpu_ar_model_runner.py` and `gpu_generation_model_runner.py`.
3. **Pure workaround, no code change:** run with `async_chunk: true` (the shipped default in `vllm_omni/deploy/qwen3_tts.yaml:14`), which was never affected.

A couple of notes so you don't chase red herrings: the `NVFP4 W4A4 weight_scale NaN-clamp` patch line and the `min_tokens: 2` / empty-audio behavior (#4962) in your environment are unrelated to this hang — the hang is purely the connector-input starvation described above. And on current `main` the connector-input timeout is `600s` (`omni_scheduler_mixin.py:37`), vs. the `300s` you saw on `0.20.2`; that's just a timeout-value change and doesn't affect the diagnosis.

**Verdict: keep closed — fixed by #4792.** Please confirm after upgrading; if you still see a Stage-1 timeout on a post-#4792 build, reopen with the served model arch/stage names and the deploy YAML so we can check the `_FULL_PAYLOAD_INPUT_STAGES` registration for your exact model.