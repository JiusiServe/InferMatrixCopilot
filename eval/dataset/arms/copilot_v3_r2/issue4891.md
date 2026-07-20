# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

> ⚠ draft shipped with caveats — agent self-assessed confidence: high; verify before relying on it.

### Root cause
`QuantizationConfig.get_cache_scale` was removed in vLLM v0.23.0 (upstream vllm#43167). PR #4810 migrated the four AR-side custom loaders to `get_cache_scale_mapper()` or deferred to `AutoWeightsLoader`, but the diffusion-side HunyuanImage3 transformer at `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py:2238` was missed and still called the removed API.

### Fix
Remove the manual `quant_config.get_cache_scale(name)` branch from `load_weights` in `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py`. The KV-cache scale names are already handled by `maybe_remap_kv_scale_name` at line 2343 on the fallthrough path. The exact diff is in PR #4808 (closed but correct).

### Workaround
Until updated to latest main: either cherry-pick the commit that removed the call, or manually delete the `if scale_name := self.quant_config.get_cache_scale(name):` block (and its body) from the `load_weights` method.

### Preconditions
vLLM >= 0.23.0 (where `get_cache_scale` was removed); any quantized HunyuanImage3 checkpoint that triggers the `load_weights` code path.

### Verification
grep -r '\.get_cache_scale(' vllm_omni/diffusion/models/hunyuan_image3/  # must return no matches; pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py -v  # all pass

### Prevention
Add `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` to the `_STALE_API_FILES` list in `tests/model_executor/models/test_kv_cache_scale_mapper.py` so the regression test covers the diffusion-side loader.

### Disposition
close

### Additional context
## Root Cause

Confirmed. vLLM removed `QuantizationConfig.get_cache_scale` in v0.23.0 (upstream [vllm#43167](https://github.com/vllm-project/vllm/pull/43167)), replacing it with `get_cache_scale_mapper()`. PR [#4810](https://github.com/vllm-project/vllm-omni/pull/4810) migrated the four AR-side custom loaders but the diffusion-side HunyuanImage3 transformer at:

```
vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py  (load_weights, line ~2238)
```

still called `self.quant_config.get_cache_scale(name)`, causing the `AttributeError` you hit.

## Fix

The exact fix is in (closed) PR [#4808](https://github.com/vllm-project/vllm-omni/pull/4808): drop the manual `get_cache_scale` branch entirely. KV-cache scale names are already handled by `maybe_remap_kv_scale_name` in the same loader (line 2343), which remaps `.output_scale` → `.attn.{k,v,q}_scale` on the fallthrough path. The manual branch was redundant and fragile.

In the current `main` tip, this call has already been removed (only a comment remains at line 2239: `# quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).`). Please `git pull` to latest main and re-test.

## Prevention

The regression test at `tests/model_executor/models/test_kv_cache_scale_mapper.py::test_model_loaders_do_not_call_removed_get_cache_scale` currently only audits the four AR-side files in `_STALE_API_FILES`. The diffusion file should be added to that list to prevent this footgun from recurring. I'll open a follow-up for that coverage gap.

## Verification

```bash
grep -r '\.get_cache_scale(' vllm_omni/
# Should return no matches (only comments/imports referencing the mapper, not the old API)

pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py -v
# All tests should pass
```
