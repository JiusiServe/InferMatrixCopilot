# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Diagnosis

The crash you hit is a known rebase-regression: vLLM removed `QuantizationConfig.get_cache_scale` in v0.23.0 (upstream PR vllm#43167), and five vllm-omni custom loaders were still calling it. The AR-side loaders were fixed in **#4810** (merged), but the DiT-side loader at `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` was missed — that's this issue.

## Current status: **already fixed on main**

Verified against the live checkout at the time of this answer:

- **File:** `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py`
- **Line 2238–2239:** The former `quant_config.get_cache_scale(name)` call is gone — replaced by a comment:
  ```python
  # KV-cache scales are renamed via maybe_remap_kv_scale_name below;
  # quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).
  ```
- **Line 2343:** KV-cache scale names are now remapped through the standard path:
  ```python
  name = maybe_remap_kv_scale_name(name, params_dict)
  ```
- **Repo-wide grep:** `.get_cache_scale(` returns **zero hits** across the entire repository.

PR **#4808** (closed, superseded) was the DiT-specific fix. PR **#4810** (merged) landed the broader fix for all five affected loaders plus regression tests in `tests/model_executor/models/test_kv_cache_scale_mapper.py`.

## Workaround

Update to current `main`:

```bash
git checkout main && git pull
```

If you're pinned to an older commit, cherry-pick the fix from #4810 or #4808.

## Verification

Run the regression suite:

```bash
pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py
```

All tests should pass, confirming zero stale `get_cache_scale` callers.

## Related

- Tracking issue: #4809
- AR-side fix (merged): #4810
- DiT-side fix (closed, superseded): #4808
- Upstream removal: vllm#43167 (vLLM v0.23.0)

If the crash still reproduces on **current main**, please re-open with the exact commit hash (`git rev-parse HEAD`) and a full traceback.
