# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4962, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root cause (confirmed)

vLLM's `MinTokensLogitsProcessor` masks `SamplingParams.all_stop_token_ids`, which unconditionally includes the **text tokenizer's EOS id** (`151645` for Qwen3-TTS). The Qwen3-TTS talker's `lm_head` outputs only **3072 logits** (codec vocabulary), so `index_put_` of `-inf` at index 151645 is out of bounds and triggers `CUDA error: device-side assert triggered`.

This is documented in the fix itself:
- **`vllm_omni/worker/sampling_utils.py:20-22`** — _"MinTokensLogitsProcessor.apply writes -inf at an out-of-range index and index_put_ triggers a CUDA device-side assert (#4962)"_

## Fix (already in tree)

A `sanitize_min_tokens_stop_ids()` guard has been added that runs before every sampling step. It drops stop ids that exceed the actual logits vocabulary from the `MinTokensLogitsProcessor`'s internal state:

- **Guard function**: `vllm_omni/worker/sampling_utils.py:14-57` — iterates `MinTokensLogitsProcessor` instances, removes any `stop_tok_ids >= logits_vocab`, and rebuilds the device-side mask slice.
- **GPU call site**: `vllm_omni/worker/gpu_ar_model_runner.py:1903-1908` — called in `sample_tokens()` after logits are computed, before `self._sample()`.
- **NPU call site**: `vllm_omni/platforms/npu/worker/npu_ar_model_runner.py:928-933` — same guard, NPU path.

Out-of-range ids are unreachable for the head, so dropping them never changes sampling or stopping behavior.

## Workaround (if stuck on an older commit)

Update to a revision that includes the `sanitize_min_tokens_stop_ids` fix. If that's not immediately possible, a temporary local workaround is to set `min_tokens: 0` in the stage-0 `default_sampling_params` (losing the early-EOS guard), or patch the Qwen3-TTS stage setup to not fold the text tokenizer EOS into `stop_token_ids`.

## Verification

Run the existing test:
```bash
pytest tests/worker/test_min_tokens_stop_ids_guard.py -v
```
All 5 tests pass, including `test_oob_stop_id_crashes_without_guard` (documents the failure mode) and `test_guard_filters_oob_and_keeps_in_range_mask` (confirms the codec EOS 2150 is still correctly masked after sanitization).

## Deployment

The Qwen3-TTS deploy YAML (`vllm_omni/deploy/qwen3_tts.yaml:60`) already includes `min_tokens: 2` for stage-0, which is correct and safe with the fix.

---

**Verdict**: The root cause analysis in the issue is accurate, and the fix is already implemented. This issue should be closed. If the crash still reproduces on a commit that includes `vllm_omni/worker/sampling_utils.py`, please reopen with the updated commit hash.

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
