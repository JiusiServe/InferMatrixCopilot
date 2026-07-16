# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root cause

vLLM removed `QuantizationConfig.get_cache_scale()` in v0.23.0 (upstream PR vllm#43167). PR #4810 migrated the AR-side custom loaders to the new `get_cache_scale_mapper()` path, but the diffusion-side HunyuanImage3 DiT transformer loader in `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` was missed and still called the old API at line ~2238.

**Mechanism**: `HunyuanImage3Model.load_weights()` had a manual branch that called `self.quant_config.get_cache_scale(name)` to short-circuit KV-cache scale loading. Since the method no longer exists on `ModelOptMixedPrecisionConfig` (or any `QuantizationConfig` subclass), any quantized checkpoint triggers `AttributeError` during weight loading in the DiT stage.

## Current status: fixed on main

On the current main branch, the offending call has been removed. Instead, KV-cache scale names flow through the standard `maybe_remap_kv_scale_name` path (line 2343):

```python
# hunyuan_image3_transformer.py, lines 2238-2239
# KV-cache scales are renamed via maybe_remap_kv_scale_name below;
# quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).
```

```python
# hunyuan_image3_transformer.py, line 2343
name = maybe_remap_kv_scale_name(name, params_dict)
```

This is exactly the fix the reporter described and verified. A regression test (`tests/model_executor/models/test_kv_cache_scale_mapper.py`) now enforces that none of the 5 affected loaders contain `.get_cache_scale(`.

## Related issues & PRs

| Link | Status | What |
|------|--------|------|
| #4809 | Issue | Umbrella tracking all 5 `get_cache_scale` call sites |
| #4810 | **MERGED** | Fixed AR-side loaders (hunyuan_image3.py, mammoth_moda2, mimo_audio, qwen2_old) |
| #4808 | **CLOSED** | DiT transformer fix (superseded — fix is on main) |
| #4806 | Issue | Original Hunyuan-image FP8 serving failure (same root cause) |
| #4597 | Open | Additional scalar-expert-scale + `<img_ratio>` fixes (complementary) |

## Workaround & verification

**Workaround**: Update to the latest main branch — the fix is already present.

```bash
git checkout main && git pull
pip install -e .
```

**Verification**: Run the regression test:

```bash
pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py
```

All 9 tests should pass on main. You can also confirm the dead call is absent:

```bash
grep -r 'get_cache_scale(' vllm_omni/ diffusion/  # should return nothing
```

## Disposition

This is a **duplicate of #4808 / #4809** — the fix is already on main. Closing. If you still see this crash on current main HEAD, please reopen with the exact commit hash.

**Disposition:** duplicate-of-#4808
