# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
The diffusion‑side `HunyuanImage3Model.load_weights` in `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` (line 2238 before the fix) called `quant_config.get_cache_scale(name)`, an API that was removed upstream in vLLM v0.23.0 (vllm#43167). The AR‑side loaders were migrated in #4810 but this call site was missed. The KV‑cache scale names are already handled by `maybe_remap_kv_scale_name` later in the same loop, making the manual branch both redundant and the source of the crash.

### Fix
Remove the manual `get_cache_scale` branch from `HunyuanImage3Model.load_weights` and let the standard `maybe_remap_kv_scale_name` fall‑through path handle quantized KV‑cache scales. This was applied in PR #4808, which is already merged on `main`. The dead call is replaced by a comment explaining the removal.

### Workaround
Update to a `main` commit that includes PR #4808. If that is not immediately possible, temporarily avoid enabling the DiT stage for quantized HunyuanImage3 checkpoints, or apply a local patch that deletes the `if self.quant_config is not None:` block that invokes `get_cache_scale` and its associated `params_dict` / `loaded_weight[0]` logic (approximately lines 2225–2250 before the fix).

### Preconditions
vLLM ≥ v0.23.0 (where `get_cache_scale` was removed); vllm‑omni build that includes the fix from PR #4808 (any recent `main` commit after the PR merge).

### Verification
Run `grep -n 'get_cache_scale(' vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py`. Only a comment should appear (no actual method call). Then serve a quantized HunyuanImage3 checkpoint with the DiT stage enabled and verify that weight loading completes without `AttributeError`.

### Prevention
Add `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` to the parametrize list in the existing regression test `tests/model_executor/models/test_kv_cache_scale_mapper.py::test_model_loaders_do_not_call_removed_get_cache_scale` so that future removals of vLLM quantization APIs are caught on both the AR and diffusion sides. Alternatively, introduce a CI lint check that greps for calls to known‑removed vLLM methods across all custom loaders.

### Disposition
duplicate-of-#4808

### Additional context
Thanks for the detailed report. This crash is already fixed on `main` and is a **duplicate of [#4808](https://github.com/vllm-project/vllm-omni/pull/4808)**.

**Root cause:** vLLM removed `QuantizationConfig.get_cache_scale()` in v0.23.0 (upstream [vllm#43167](https://github.com/vllm-project/vllm/pull/43167)). The autoregressive‑side loaders were migrated in [#4810](https://github.com/vllm-project/vllm-omni/pull/4810), but the diffusion‑side `HunyuanImage3Model.load_weights` in `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` was missed and still called the removed API, causing the `AttributeError`.

**Fix:** PR #4808 removed the dead manual `get_cache_scale` branch. KV‑cache scale names are now handled correctly by `maybe_remap_kv_scale_name` further down in the same loader. The former call site (line 2238) now contains only a comment:

```python
# KV-cache scales are renamed via maybe_remap_kv_scale_name below;
# quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).
```

**What to do:** Update to any `main` commit that includes PR #4808. If you are unable to update immediately, the **workaround** is to locally delete the `if self.quant_config is not None:` block that calls `get_cache_scale` and its associated `params_dict`/`loaded_weight[0]` logic (roughly lines 2225‑2250 before the fix).

**Verification:** After updating, confirm the call no longer exists:
```bash
grep -n 'get_cache_scale(' vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py
```
Only a comment should appear. Then serve a quantized HunyuanImage3 checkpoint with the DiT stage enabled — weight loading will succeed without the `AttributeError`.

Closing as a duplicate of #4808.

> ⚠ merge-state statements above were not verified via gh this run — treat as unconfirmed.
