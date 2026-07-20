# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
vLLM upstream removed `QuantizationConfig.get_cache_scale` in v0.23.0 (upstream PR vllm#43167). The diffusion-side HunyuanImage3 DiT loader at `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py:2238` still called `self.quant_config.get_cache_scale(name)` in its `load_weights` method. PR #4810 fixed the AR-side loaders but missed this diffusion-side file.

### Fix
Delete the manual `get_cache_scale` branch from `HunyuanImage3Model.load_weights` in `hunyuan_image3_transformer.py`. KV-cache scale names are already handled by the existing `maybe_remap_kv_scale_name(name, params_dict)` fall-through at line 2343 and the outer `AutoWeightsLoader`. This is exactly what PR #4808 does.

### Workaround
Update to latest main (post PR #4808), or cherry-pick the PR #4808 commit. Alternatively, apply the minimal fix: in `hunyuan_image3_transformer.py:HunyuanImage3Model.load_weights`, remove the `get_cache_scale` branch entirely — the comment at lines 2238-2239 already documents the removal, and the `maybe_remap_kv_scale_name` call at line 2343 handles KV-cache scales on the fall-through path.

### Preconditions
Any quantized HunyuanImage3 checkpoint (ModelOpt mixed FP8/NVFP4 or other quantization configs that hit the `get_cache_scale` path). vLLM >= 0.23.0. The fix has no hardware/weight-specific preconditions — it's a pure API-removal cleanup.

### Verification
grep -r '\.get_cache_scale(' vllm_omni/   # must return zero matches

### Prevention
When upstream vLLM removes or renames a public API, run a repo-wide grep for the old name across ALL loaders — not just `model_executor/models/` but also `diffusion/models/` and any vendored code. PR #4810's regression test (`test_kv_cache_scale_mapper.py`) already caught the diffusion-side survivor (see its CI failure log), proving that a grep-based test can prevent recurrence. Consider adding `tests/model_executor/models/test_kv_cache_scale_mapper.py` as a CI gate.

### Disposition
duplicate-of-#4808

### Additional context
## Root cause

vLLM removed `QuantizationConfig.get_cache_scale` in v0.23.0 (upstream PR [vllm#43167](https://github.com/vllm-project/vllm/pull/43167)), replacing it with `get_cache_scale_mapper()`. The AR-side HunyuanImage3 loader was fixed in **PR #4810** (merged), but the **diffusion-side** DiT loader at `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` was missed and still called the dead API:

```
File "vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py", line 2238, in load_weights
AttributeError: 'ModelOptMixedPrecisionConfig' object has no attribute 'get_cache_scale'
```

## Fix

This was addressed by **PR #4808** ([HunyuanImage3 DiT: drop redundant manual KV-cache scale loading](https://github.com/vllm-project/vllm-omni/pull/4808)). The fix removes the manual `get_cache_scale` branch entirely — KV-cache scale names are already handled by the existing `maybe_remap_kv_scale_name` call at line 2343 in the same `load_weights` method, plus the outer `AutoWeightsLoader` that wraps this loader.

**Current state**: `grep -r '\.get_cache_scale(' vllm_omni/` returns zero matches — both PR #4810 (AR side) and PR #4808 (DiT side) fixes are present in the current main branch.

## Workaround

If you cannot update to latest main, cherry-pick the fix from PR #4808: in `hunyuan_image3_transformer.py:HunyuanImage3Model.load_weights`, delete the `get_cache_scale` manual branch. The comment at line 2238-2239 already documents the removal:

```python
# KV-cache scales are renamed via maybe_remap_kv_scale_name below;
# quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).
```

The fall-through path with `maybe_remap_kv_scale_name(name, params_dict)` at line 2343 handles all KV-cache scale names correctly.

## Verification

```bash
# Confirm no remaining calls to the removed API:
grep -r '\.get_cache_scale(' vllm_omni/
# Expected output: (no matches)

# Serve a quantized HunyuanImage3 checkpoint:
# The DiT worker should load weights without AttributeError.
```

## Related

- **PR #4808** — DiT/diffusion-side fix (this bug)
- **PR #4810** — AR-side fix for `hunyuan_image3.py`, `mammoth_moda2.py`, `mimo_audio_llm.py`, `qwen2_old.py` (merged)
- **Issue #4809** — tracking issue for all `get_cache_scale` call sites
- **Issue #4806** — original Hunyuan-image FP8 serving failure report

Marking as **duplicate of #4808** — the fix is already in the codebase.
