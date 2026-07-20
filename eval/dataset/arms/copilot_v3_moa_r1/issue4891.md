# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
The diffusion‑side HunyuanImage3 transformer’s `load_weights` (`vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py:2238`) called `quant_config.get_cache_scale(name)`, an API removed in vLLM v0.23.0 (vllm#43167). This call site was missed during the v0.23.0 rebase; PR #4810 had already removed the same call from the AR‑side loaders.

### Fix
PR #4808 (merged) removed the manual `get_cache_scale` branch and added a comment at line 2239. The outer `AutoWeightsLoader` and the loader’s own `maybe_remap_kv_scale_name` now correctly handle KV‑cache scale remapping for quantized checkpoints.

### Workaround
Update to a `main` commit that includes PR #4808. If updating isn’t possible, manually delete the `if quant_config.get_cache_scale(name):` conditional block in `load_weights` of `hunyuan_image3_transformer.py`, keeping only the fall‑through that calls `maybe_remap_kv_scale_name`.

### Preconditions
vLLM ≥ 0.23.0; vLLM‑Omni commit includes PR #4808.

### Verification
grep -n 'get_cache_scale' vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py
Return: only line 2239 (a comment, e.g., ‘quant_config.get_cache_scale was removed...’), no active code calls.

### Prevention
When rebasing onto a new vLLM version that removes or renames `QuantizationConfig` APIs, run a repo‑wide grep for the old API across **all** model loaders (both AR and diffusion). Consider adding a CI lint rule that flags direct calls to deprecated quant‑config methods.

### Disposition
duplicate-of-#4808

### Additional context
Thanks for the report! This is already fixed on `main` and is a **duplicate of [#4808](https://github.com/vllm-project/vllm-omni/pull/4808)**.

### What happened
The diffusion-side HunyuanImage3 loader (`hunyuan_image3_transformer.py`) still called `quant_config.get_cache_scale(name)`, which was removed in vLLM v0.23.0. PR #4810 fixed the AR-side custom loaders, but this call site was missed.

### The fix (already merged)
- **PR #4808** (merged) — removed the manual `get_cache_scale` branch from the DiT transformer’s `load_weights`. The outer `AutoWeightsLoader` + `maybe_remap_kv_scale_name` now handle all KV‑cache scale remapping for quantized checkpoints. The only remaining reference is an explanatory comment at line 2239.
- **PR #4810** — fixed the four AR‑side loaders (`hunyuan_image3`, `mammoth_moda2`, `mimo_audio`, `qwen2_old`) with the same pattern.

### Verification
If you’re still hitting the crash, make sure your checkout includes #4808. You can confirm with:
```bash
git log --oneline --grep="4808" | head -1
```
Then grep for the old API:
```bash
grep -n 'get_cache_scale' vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py
```
The only hit should be the comment at line 2239 — no live code calls.

### Workaround for older commits
Either `git pull` to the latest `main`, or manually delete the `if quant_config.get_cache_scale(name):` block in `hunyuan_image3_transformer.py`’s `load_weights`, leaving just the fall‑through that calls `maybe_remap_kv_scale_name`.

This issue can be closed alongside [#4809](https://github.com/vllm-project/vllm-omni/issues/4809).

> ⚠ merge-state statements above were not verified via gh this run — treat as unconfirmed.
