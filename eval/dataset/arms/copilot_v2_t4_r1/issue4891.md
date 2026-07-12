# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root cause

`vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` — the `HunyuanImage3Model.load_weights` method (line 2125) had a manual branch that called:

```python
self.quant_config.get_cache_scale(name)
```

This API was removed from vLLM upstream in [vllm#43167](https://github.com/vllm-project/vllm/pull/43167) (first released in v0.23.0rc2 / v0.23.0). vLLM-Omni picked up the removal in the v0.23.0 rebase (PR #4286). PR #4810 fixed the 4 AR-side custom loaders that still called it, but the diffusion-side HunyuanImage3 DiT loader was the 5th call site and was missed.

## Current state

On current `main` this is **already fixed**. The `get_cache_scale` call has been removed and replaced with:

- A comment at lines 2238-2239 explaining the removal
- Reliance on `maybe_remap_kv_scale_name` (imported from `vllm.model_executor.model_loader.weight_utils`) at line 2343, which handles KV-cache scale name remapping without the removed API

The DiT is loaded through an outer `AutoWeightsLoader` in `pipeline_hunyuan_image3.py:458`, which already remaps `.output_scale` → `.attn.{k,v,q}_scale` before delegating to this loader — so the manual branch was redundant anyway (this is the same rationale as the AR-side fix in #4810).

## Fix / workaround

**Update past commit 86bdcaf3d.** The fix is already on main. If you cannot update immediately, the one-line workaround is to delete the `get_cache_scale` branch from `load_weights` — the same change that #4808 proposed:

```diff
-            scale_name = self.quant_config.get_cache_scale(name)
-            if scale_name is not None:
-                param = params_dict[scale_name]
-                weight_loader(param, loaded_weight)
-                return
```

(The existing `maybe_remap_kv_scale_name` call later in the same method handles quantized checkpoints correctly on its own.)

## Verification

```bash
# Confirm the call is gone:
grep -rn 'get_cache_scale(' vllm_omni/
# Should return zero matches.

# Run the existing regression suite:
pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py -v
```

## Related

- **PR #4810** (merged): AR-side fix — `hunyuan_image3.py`, `mammoth_moda2.py`, `mimo_audio_llm.py`, `qwen2_old.py`
- **PR #4808** (closed): originally proposed this DiT-side fix
- **Issue #4809**: broader tracking issue for all `get_cache_scale` call sites
- **Issue #4806**: original Hunyuan-image FP8 serving failure report
