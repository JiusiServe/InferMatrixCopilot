# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4962, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root cause confirmed

Your diagnosis is exactly right. The crash path is:

1. vLLM's input processor calls `SamplingParams.update_from_generation_config({}, eos_token_id=151645)`, which unconditionally adds the text-tokenizer EOS (151645) to `all_stop_token_ids`.
2. When `min_tokens >= 1`, a `MinTokensLogitsProcessor` is created and its `apply()` does `index_put_` to write `-inf` into a logits tensor of shape `[batch, 3072]` at every stop-token id — including 151645.
3. 151645 ≥ 3072 → out-of-range → CUDA device-side assert → `EngineDeadError`.

## Fix (already in tree)

A guard, `sanitize_min_tokens_stop_ids()`, was added in **`vllm_omni/worker/sampling_utils.py:14`**. It runs at the top of every `sample_tokens()` call in both GPU and NPU AR runners and drops any stop-token IDs that are ≥ the logits vocabulary size from the `MinTokensLogitsProcessor` internal state. Out-of-range IDs are unreachable for the head anyway, so this never changes sampling or stopping behavior.

**Call sites:**
- `GPUARModelRunner.sample_tokens()` → `vllm_omni/worker/gpu_ar_model_runner.py:1906`
- `NPUARModelRunner.sample_tokens()` → `vllm_omni/platforms/npu/worker/npu_ar_model_runner.py:931`

**Tests:** `tests/worker/test_min_tokens_stop_ids_guard.py` (5 tests, `pytest -m core_model`).

## Current deploy config

The bundled `vllm_omni/deploy/qwen3_tts.yaml` already ships `min_tokens: 2` in stage-0 `default_sampling_params`:

```yaml
stages:
  - stage_id: 0
    default_sampling_params:
      temperature: 0.9
      top_k: 50
      max_tokens: 4096
      min_tokens: 2          # ← now safe; see #4962
      repetition_penalty: 1.05
```

## Workaround (if you're on an older commit)

Before the fix landed (commit d365d3a6), the talker stage crashes with any `min_tokens >= 1`. Workarounds:

1. **Rebase to current main** — the fix is in-tree.
2. **Cherry-pick** `vllm_omni/worker/sampling_utils.py` plus the two one-line calls in the GPU/NPU runners.
3. **Avoid `min_tokens` entirely** on the talker stage (but then some checkpoints sample codec EOS on frame 0 → empty audio).

## Verification

```bash
# Run the targeted unit tests (CPU-safe, no GPU needed):
pytest tests/worker/test_min_tokens_stop_ids_guard.py -v -m core_model

# Full integration: launch Qwen3-TTS with the bundled deploy config
vllm serve Qwen/Qwen3-TTS-0.6B --omni --deploy-config vllm_omni/deploy/qwen3_tts.yaml
```

The engine should start cleanly and the first TTS request should produce audio (not crash on `min_tokens`).

## Linked issues/PRs

- Issue #4962 (this issue)
- The fix references #4962 in comments/docs in `sampling_utils.py`, `test_min_tokens_stop_ids_guard.py`, `gpu_ar_model_runner.py`, `npu_ar_model_runner.py`, and `qwen3_tts.yaml`.

---

**Disposition:** close — the fix is in-tree and the bundled deploy config works. Reopen if the crash reproduces on current `main` after a clean build.

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
