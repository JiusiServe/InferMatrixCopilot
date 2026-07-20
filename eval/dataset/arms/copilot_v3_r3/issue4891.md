# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
PR #4810 (the `get_cache_scale` co-change sweep) enumerated and fixed the four AR-side loaders in `vllm_omni/model_executor/models/` but did not sweep `vllm_omni/diffusion/` — the fifth call site in `hunyuan_image3_transformer.py:2238` (reporter's commit 86bdcaf3d) was an unswept survivor. Evidence: the PR #4810 diff touches only files under `vllm_omni/model_executor/models/` and the test file; `vllm_omni/diffusion/` is absent.

### Fix
Remove the `quant_config.get_cache_scale(name)` branch from `HunyuanImage3Model.load_weights` in `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py`. The outer `AutoWeightsLoader` already remaps KV-cache scale names before delegating, and the fall-through path calls `maybe_remap_kv_scale_name`. PR #4808 implements this fix and it is already present on current main.

### Workaround
Update to latest `main` (the fix is already landed). If rebasing is not possible, cherry-pick the commit from PR #4808.

### Preconditions
Must be on a main revision that includes the fix from PR #4808 (or equivalent). The reporter's commit 86bdcaf3d predates this fix.

### Verification
grep -r '\.get_cache_scale(' vllm_omni/ tests/  # expected: no output

### Prevention
Add `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` to `_STALE_API_FILES` in `tests/model_executor/models/test_kv_cache_scale_mapper.py` so the regression test covers the diffusion-side loader and catches future reintroductions of the removed API.

### Disposition
close / duplicate-of-#4809 — reopen if `grep -r '\.get_cache_scale(' vllm_omni/` returns any hits on latest main

### Additional context
## Root Cause

`vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` (line ~2238 in your commit `86bdcaf3d`) called `self.quant_config.get_cache_scale(name)` — an API that vLLM removed in v0.23.0 (upstream PR [#43167](https://github.com/vllm-project/vllm/pull/43167)). PR [#4810](https://github.com/vllm-project/vllm-omni/pull/4810) migrated the four AR-side custom loaders (`hunyuan_image3.py`, `mammoth_moda2.py`, `mimo_audio_llm.py`, `qwen2_old.py`) but missed this fifth call site in the DiT/diffusion loader.

## Fix (already on main)

PR [#4808](https://github.com/vllm-project/vllm-omni/pull/4808) removed the redundant manual KV-cache scale loading branch from `HunyuanImage3Model.load_weights`. The fix is already present on current `main`: the dead call has been removed and the comment at line 2239 documents the removal:

```python
# KV-cache scales are renamed via maybe_remap_kv_scale_name below;
# quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).
```

KV-cache scale names are already remapped by the outer `AutoWeightsLoader` (in `pipeline_hunyuan_image3.py`) before delegating to this loader, and the fall-through path already calls `maybe_remap_kv_scale_name`, so the manual branch was both redundant and fragile.

## Workaround

Update to latest `main`. If you cannot rebase immediately, cherry-pick the commit from [#4808](https://github.com/vllm-project/vllm-omni/pull/4808) onto your tree.

## Verification

```bash
# Confirm zero remaining call sites of the removed API:
grep -r '\.get_cache_scale(' vllm_omni/ tests/
# Expected: no output (empty)
```

## Prevention

The regression test added in #4810 (`tests/model_executor/models/test_kv_cache_scale_mapper.py`) currently checks only the four AR-side loaders. The diffusion transformer file should be added to `_STALE_API_FILES` to prevent future regressions:

```python
_STALE_API_FILES = [
    "vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py",
    "vllm_omni/model_executor/models/mammoth_moda2/mammoth_moda2.py",
    "vllm_omni/model_executor/models/mimo_audio/mimo_audio_llm.py",
    "vllm_omni/model_executor/models/qwen2_5_omni/qwen2_old.py",
+   "vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py",  # ← missing
]
```

## Related

- Tracking issue: [#4809](https://github.com/vllm-project/vllm-omni/issues/4809) (all 5 `get_cache_scale` call sites)
- AR-side fix: [#4810](https://github.com/vllm-project/vllm-omni/pull/4810) (MERGED)
- DiT-side fix: [#4808](https://github.com/vllm-project/vllm-omni/pull/4808) (CLOSED, fix landed on main)
