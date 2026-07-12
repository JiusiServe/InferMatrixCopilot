# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4962, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root-cause confirmed: text tokenizer EOS leaks into codec talker's min-tokens mask

Your diagnosis is correct. Here's the full mechanism with file:line citations.

### 1. How the text EOS gets folded in

vLLM's `InputProcessor.process_inputs()` calls `update_from_generation_config` for every request:

```python
# /rebase/vllm/vllm/v1/engine/input_processor.py:323
sampling_params.update_from_generation_config(
    self.generation_config_fields,
    self.renderer.get_eos_token_id(),
)
```

This adds the text tokenizer's EOS id (151645 for Qwen3-TTS) to `SamplingParams._all_stop_token_ids` (see `/rebase/vllm/vllm/sampling_params.py:639`). The Qwen3-TTS pipeline correctly declares `stop_token_ids: [2150]` (the codec EOS) in `sampling_constraints` (`vllm_omni/model_executor/models/qwen3_tts/pipeline.py:30`), but `update_from_generation_config` appends the text EOS regardless.

### 2. How it crashes

`MinTokensLogitsProcessor.add_request()` captures `params.all_stop_token_ids` (`/rebase/vllm/vllm/v1/sample/logits_processor/builtin.py:195`). On `apply()` (line 218), it writes `-inf` at every stop token id via `logits.index_put_(self.logits_slice, self.neg_inf_tensor)`. The talker's lm_head has `vocab_size=3072` (`qwen3_tts_talker.py:358` — `self.talker_config.vocab_size`), so index 151645 is out of range → CUDA device-side assert.

### 3. Fix already in the codebase

A guard function `sanitize_min_tokens_stop_ids()` was added in `vllm_omni/worker/sampling_utils.py` (whole file — 49 LOC). It iterates `MinTokensLogitsProcessor` state, drops any stop token id ≥ the actual logits vocabulary size, and rebuilds the device-side mask slice. It is called:

- **GPU runner**: `gpu_ar_model_runner.py:1906` — right before `_sample()`
- **NPU runner**: `npu_ar_model_runner.py:931` — same location

Dedicated tests exist at `tests/worker/test_min_tokens_stop_ids_guard.py` with five test functions covering the crash-without-guard, guard-filtering, no-op for in-range ids, one-time sanitization, and multi-request scenarios.

### 4. Workaround (if you cannot rebase yet)

As a temporary workaround, set `stop_token_ids` in your deploy YAML's `default_sampling_params` for stage 0 to only include valid codec stop ids (i.e., `[2150]`) and avoid setting any `stop` strings that would cause the tokenizer to encode additional stop tokens. However, this won't prevent the text EOS folding because it's added by the engine's `update_from_generation_config` call — the only reliable fix is the `sanitize_min_tokens_stop_ids` guard in the runner.

### 5. Verification

```bash
# Run the dedicated guard tests
cd tests/worker && python -m pytest test_min_tokens_stop_ids_guard.py -v

# Or reproduce the original failure mode (CPU-safe, no CUDA needed):
python -c "
import torch
from vllm import SamplingParams
from vllm.v1.sample.logits_processor import BatchUpdate, MinTokensLogitsProcessor

params = SamplingParams(min_tokens=2, stop_token_ids=[2150])
params.update_from_generation_config({}, 151645)
proc = MinTokensLogitsProcessor(None, device=torch.device('cpu'), is_pin_memory=False)
proc.update_state(BatchUpdate(batch_size=1, removed=[], added=[(0, params, None, [])], moved=[]))
logits = torch.zeros(1, 3072)
try:
    proc.apply(logits)
    print('UNEXPECTED: no crash — guard may already be active')
except (IndexError, RuntimeError):
    print('Confirmed: index_put_ fails with text EOS 151645 on vocab=3072')
"
```

Please rebase to current main and re-test. If the issue persists after rebase, please provide the full traceback and your deploy YAML's stage-0 `default_sampling_params` section.

**Disposition:** keep-open

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
