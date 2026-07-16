I have everything I need. Both loaders in the checkout already carry the fix, and there's a regression test. Here is my maintainer answer for issue #4806.

---

## Answer to #4806 — "[Bug]: Hunyuan-image fp8 cannot serve"

Thanks for the report, and thanks @akshatvishu / @lishunyang12 for the accurate triage. This is confirmed as a **weight-loading API drift**, not a Hunyuan-image modeling bug. It's fully resolved and can be **closed as a duplicate of #4809** (fixes landed in **#4808** + **#4810**).

### Root cause

vLLM PR [vllm-project/vllm#43167](https://github.com/vllm-project/vllm/pull/43167) (shipped in vLLM v0.23.0) removed the per-weight helper `quant_config.get_cache_scale(name)` and moved KV-cache scale remapping up into the `AutoWeightsLoader` path via a new `quant_config.get_cache_scale_mapper()`. Any vllm-omni loader that still called the removed method would raise `AttributeError` the moment `quant_config` is non-`None` — i.e. exactly when you enable FP8. That's why serving works in bf16/fp16 but dies on `--quantization fp8`.

The Hunyuan-image model exposes **two** independent weight loaders, and both had the stale call:

1. **AR / language-tower loader** — `HunyuanModel.load_weights` in `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:151`. This is invoked through the outer `AutoWeightsLoader` (`HunyuanImage3ForCausalLM.load_weights`, `hunyuan_image3.py:2169`), so it must *not* do its own cache-scale handling — the outer loader's mapper already renames `…k_proj.output_scale → …attn.k_scale`. Fixed in **#4810**; the old branch is now just a comment at `hunyuan_image3.py:225-226`.

2. **DiT transformer loader** — `HunyuanImage3Transformer2DModel.load_weights` in `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py`. This one loads weights directly (not via `AutoWeightsLoader`), so it remaps the scale names itself with `maybe_remap_kv_scale_name(name, params_dict)` at `hunyuan_image3_transformer.py:2343` (import at line 50, comment at 2238-2239). Fixed in **#4808**.

### Verification in the current tree

Both call sites are gone and there's a regression guard: `tests/model_executor/models/test_kv_cache_scale_mapper.py` asserts none of the affected loaders contain `.get_cache_scale(` (line 81) and drives each loader with a fake `quant_config` that only exposes `get_cache_scale_mapper()` to prove the mapped `…attn.k_scale` name loads correctly (lines 99-148). Hunyuan-image AR is covered explicitly (`_FakeHunyuanModel`, lines 60-74, 88-91).

### Fix / workaround for users

- **Recommended:** update to a build that includes #4808 + #4810 (both merged). No config change is needed after that.
- **If you must run an older checkout:** the minimal patch is to delete the `get_cache_scale(name)` branch in each loader and rely on the new mapper — for the AR loader let the outer `AutoWeightsLoader` handle it (no local scale code), and for the DiT loader replace it with `name = maybe_remap_kv_scale_name(name, params_dict)` before the parameter lookup, skipping when it returns `None`.

### One caveat for mixed-precision checkpoints

If you're loading a *mixed* ModelOpt **FP8/NVFP4** Hunyuan-image checkpoint (not the plain FP8 case in this issue), two additional fixes are needed beyond the above: handling scalar (`ndim == 0`) per-expert scale tensors, and the `<img_ratio>` tokenizer-token guard. Those are carried in **#4597** and should be trimmed down to just those two once #4808/#4810 land — otherwise plain FP8 already serves.

**Disposition:** duplicate of **#4809**, resolved by **#4808** + **#4810** → close.