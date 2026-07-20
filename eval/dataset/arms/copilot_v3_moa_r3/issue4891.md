# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
vLLM v0.23.0 (vllm#43167) removed `QuantizationConfig.get_cache_scale` in favor of `get_cache_scale_mapper()` + `maybe_remap_kv_scale_name`. The HunyuanImage3 DiT loader in `hunyuan_image3_transformer.py` (old line ~2238) had a manual `self.quant_config.get_cache_scale(name)` branch that wasn't swept during the API migration. PR #4810 swept the AR-side loaders; PR #4808 swept the DiT loader. Both fixes are now on main.

### Fix
Already applied on main: the manual `get_cache_scale` branch in `HunyuanImage3Model.load_weights` was removed. KV-cache scale names are now handled by `maybe_remap_kv_scale_name` on the fall-through path (line 2343), which is the correct approach since the outer `AutoWeightsLoader` in `pipeline_hunyuan_image3.py` already remaps scale names before delegating.

### Workaround
Pull latest main and rebuild. If stuck on an older commit, cherry-pick the diff from PR #4808: remove the `if self.quant_config is not None:` block that calls `quant_config.get_cache_scale(name)` inside `load_weights` — the fall-through `maybe_remap_kv_scale_name` path handles it.

### Preconditions
vLLM-Omni main at or after the merge of PR #4810 (which landed alongside #4808). vLLM ≥ 0.23.0. Quantized HunyuanImage3 ModelOpt checkpoint (experts NVFP4 W4A4, dense FP8) with AR+DiT deploy config.

### Verification
grep -rn 'get_cache_scale[^(mapper]' vllm_omni/ — must produce zero live calls (comment-only hits are fine)

### Prevention
Add a lint/CI guard: grep for bare `get_cache_scale(` (not `get_cache_scale_mapper`) in all `vllm_omni/` loaders and fail CI if found. The test added in PR #4810 (`test_kv_cache_scale_mapper.py`) was demonstration-only and removed — a permanent regression test that greps for the dead API across all model loader files would prevent recurrence.

### Disposition
close

### Additional context
## Diagnosis

This is a real bug — but it's already fixed on `main`. The crash you hit:

```
AttributeError: 'ModelOptMixedPrecisionConfig' object has no attribute 'get_cache_scale'
```

comes from a stale manual KV-cache scale loading branch in `HunyuanImage3Model.load_weights` in `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py`. vLLM removed `QuantizationConfig.get_cache_scale` in [vllm#43167](https://github.com/vllm-project/vllm/pull/43167) (first released in v0.23.0), replacing it with `get_cache_scale_mapper()` and the `maybe_remap_kv_scale_name` path.

## What was fixed

- **PR #4810** (MERGED) — Fixed the 4 AR-side loaders that still called the removed API: `hunyuan_image3.py`, `mammoth_moda2.py`, `mimo_audio_llm.py`, `qwen2_old.py`. These now either use `get_cache_scale_mapper()` or delegate to the outer `AutoWeightsLoader`.
- **PR #4808** (CLOSED, but fix applied) — Removed the exact manual `get_cache_scale` branch you hit in the DiT transformer (`hunyuan_image3_transformer.py`). The DiT is loaded through an outer `AutoWeightsLoader` (in `pipeline_hunyuan_image3.py`), which already remaps `.output_scale` → `.attn.{k,v,q}_scale` before delegating to this loader. The same loader already calls `maybe_remap_kv_scale_name` on the fall-through path (line 2343), so the manual branch was redundant.

**Evidence on current main:** a repo-wide grep for `get_cache_scale` finds zero live calls — only the comment at line 2239:
```python
# quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).
```

## Verification

```bash
# Confirm no dead calls remain
grep -rn 'get_cache_scale[^(mapper]' vllm_omni/
# Should produce NO output (or only comments)

# End-to-end smoke (requires GPU + checkpoint)
pytest tests/diffusion/models/hunyuan_image3/ -v 2>&1 | head
```

## Disposition

This is a **duplicate of #4809** (parent tracking issue for all 5 call sites). The DiT-specific fix landed via #4808. Please pull latest `main`, rebuild, and retry — the crash should be gone. If it persists, double-check you're not running a stale `.pyc` cache:
```bash
find . -name '*.pyc' -delete && find . -name '__pycache__' -type d -exec rm -rf {} +
```

---
_Verified against current main checkout. Cross-ref: #4806 (original Hunyuan-image FP8 serving failure), #4808 (DiT fix), #4809 (parent), #4810 (AR fix)._
