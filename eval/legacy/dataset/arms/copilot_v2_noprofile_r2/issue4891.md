# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Diagnosis

The `get_cache_scale` call you reported at `hunyuan_image3_transformer.py:2238` has already been removed from the current `main` branch. I verified this on the live checkout:

- A repo-wide search (`grep -r '\.get_cache_scale(' vllm_omni/`) returns **zero matches** — the removed vLLM API is no longer called anywhere in vllm-omni.
- In the specific file, line 2238–2239 is now only a comment:
  ```python
  # KV-cache scales are renamed via maybe_remap_kv_scale_name below;
  # quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).
  ```
- The fall-through path at line 2343 correctly uses `maybe_remap_kv_scale_name(name, params_dict)` (from vLLM's `weight_utils`), which is the replacement API.

## Background

- vLLM removed `QuantizationConfig.get_cache_scale` in v0.23.0 (vllm#43167).
- **#4810** (merged) fixed the AR-side loaders in `model_executor/models/`.
- The diffusion-side loader (`diffusion/…/hunyuan_image3_transformer.py`) — the 5th call site — was initially addressed by **#4808** (now closed), but the fix has since landed on `main`.

## What to do

```bash
# Pull latest main — the fix is already there
git checkout main && git pull

# Verify the fix yourself
grep -r '\.get_cache_scale(' vllm_omni/   # should output nothing
```

## Related

- Fixes the same class of bug as #4809 and #4806.
- The regression test at `tests/model_executor/models/test_kv_cache_scale_mapper.py` covers the AR-side files but not this diffusion-side file — a minor coverage gap worth noting for maintainers.

**Verdict:** already fixed on main. Closing.

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
