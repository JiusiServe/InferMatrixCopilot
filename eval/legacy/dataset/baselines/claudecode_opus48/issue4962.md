I have everything I need. Here is the maintainer response.

---

## Answer to #4962 — Qwen3-TTS `min_tokens` on the talker stage crashes with a CUDA device-side assert

**Status: this is a real bug, your root-cause analysis is correct, and it's now fixed on `main`.** Thanks for the unusually precise report — you diagnosed it exactly.

### Confirming the root cause

Your diagnosis is spot-on. The talker stage (`stage_id=0`) runs an AR head over the **narrow RVQ codec vocabulary**. In `configuration_qwen3_tts.py:379` the talker `vocab_size=3072`, and the pipeline declares the codec EOS as the only valid stop:

```python
# vllm_omni/model_executor/models/qwen3_tts/pipeline.py:30-33
sampling_constraints={
    "detokenize": False,
    "stop_token_ids": [2150],
},
```

The problem is upstream of us: when the engine builds `SamplingParams`, `update_from_generation_config(...)` folds the **stage tokenizer's EOS id (`151645`)** into `all_stop_token_ids`, regardless of how wide the actual `lm_head` is. When `min_tokens >= 1`, vLLM's `MinTokensLogitsProcessor` builds a `(req, tok)` index and does an `index_put_(-inf)` over the sampled logits — which are only `3072` wide for the talker. Writing at index `151645` into a `[B, 3072]` tensor is out of bounds, so `index_put_` trips the device-side assert and takes EngineCore (and thus stage-0) down on the first request. Exactly the failure mode you described.

### The fix (merged)

Rather than special-casing qwen3-tts, we added a general guard that runs on every AR stage right before sampling, keyed on the *true* head width (`logits.shape[-1]`), so it also covers finetuned checkpoints and any other narrow-head codec talker:

- **`vllm_omni/worker/sampling_utils.py`** — `sanitize_min_tokens_stop_ids(logitsprocs, logits_vocab)`: walks the active `MinTokensLogitsProcessor`, drops any stop id `>= logits_vocab` from the per-request mask state, and rebuilds the device-side `logits_slice` only when something was actually out of range. Out-of-range ids are unreachable for the head, so dropping them cannot change sampling or stopping behavior. The stop-id set is mutated in place (shared with the request's `SamplingParams`), so each request is sanitized at most once.
- Wired into the GPU runner at **`vllm_omni/worker/gpu_ar_model_runner.py:1905-1909`** (just before `self._sample(...)`) and the NPU runner at **`vllm_omni/platforms/npu/worker/npu_ar_model_runner.py:931`**.
- Regression coverage in **`tests/worker/test_min_tokens_stop_ids_guard.py`** — including `test_oob_stop_id_crashes_without_guard` (documents the raw failure), `test_guard_filters_oob_and_keeps_in_range_mask` (codec EOS `2150` still masked, text EOS `151645` dropped), a full-width no-op case, idempotency, and a multi-request batch case.

We chose this over your two suggested fixes deliberately. Not folding the text EOS into `all_stop_token_ids` at talker-`SamplingParams` construction, or intersecting against `talker_config.vocab_size`, both work but require per-pipeline plumbing and would need to be repeated for every codec talker (CosyVoice3, GLM-TTS, Higgs, MOSS, etc.). The runner-level guard keyed on `logits.shape[-1]` fixes the whole class of narrow-head stages in one place and can't drift out of sync with a model's real head width.

### What this means for you

- You can now set `min_tokens: 2` (or any `min_tokens >= 1`) in the stage-0 talker `default_sampling_params` to align with the `qwen_tts` reference behavior and stop the "codec EOS on the first frame → empty audio → `HTTP 400 TTS model did not produce audio output`" case. The engine no longer crashes; the folded text EOS is silently dropped and only the codec EOS `2150` is enforced as a stop, which is the correct behavior for the talker.
- You'll see a one-time `warning_once` noting the out-of-vocab stop ids that were dropped — that's expected and harmless.
- **Action:** update to a build that includes the `sampling_utils` guard (the checkout I verified against has it on `main`; the version you reported, talker `d365d3a6` / vllm `0.24.0`, predates it). If you must stay on your current build, the interim workaround is your own suggestion — override the talker stage so the text tokenizer EOS is not folded into the stop set — but upgrading is the clean fix.

Closing as resolved. If you still hit a device-side assert on `min_tokens` after upgrading, please reopen with the talker's real `logits.shape[-1]` and the offending stop-id set and we'll dig in.