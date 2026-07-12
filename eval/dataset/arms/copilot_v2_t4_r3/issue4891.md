# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Duplicate — fixed by PR #4808 (merged)

This exact crash (`AttributeError: 'ModelOptMixedPrecisionConfig' object has no attribute 'get_cache_scale'`) was fixed by **#4808** ("[Bugfix] HunyuanImage3 DiT: drop redundant manual KV-cache scale loading"), now merged into main.

### Root cause

vLLM upstream PR [#43167](https://github.com/vllm-project/vllm/pull/43167) removed `QuantizationConfig.get_cache_scale()` in v0.23.0, replacing it with `get_cache_scale_mapper()`. The DiT transformer loader at `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py:2238` still called the removed API in a manual KV-cache scale loading branch.

### What the fix does

PR #4808 removes the manual `get_cache_scale` branch entirely. The DiT is loaded through an outer `AutoWeightsLoader` (in `pipeline_hunyuan_image3.py`) that already remaps `.output_scale` → `.attn.{k,v,q}_scale` before delegating to this loader, and the same loader already calls `maybe_remap_kv_scale_name` on the fall-through path. The manual branch was redundant.

### Current state (verified on main)

- The transformer file now has only a comment at line 2239: `# quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).`
- No call to `.get_cache_scale(` remains anywhere in the file.
- The companion PR **#4810** applies the same fix to the AR-side loaders (`hunyuan_image3.py`, `mammoth_moda2.py`, `mimo_audio_llm.py`, `qwen2_old.py`).
- Regression tests in `tests/model_executor/models/test_kv_cache_scale_mapper.py` enforce the fix across all five affected loaders.

### Workaround

Update to latest main to pick up PRs #4808 and #4810:

```bash
git checkout main && git pull
```

### Verification

Confirm the stale API call is absent:

```bash
grep -r 'get_cache_scale(' vllm_omni/
# Should return nothing (only comments referencing the removed API)
```

Or run the regression test:

```bash
pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py
```

### Linked

- **#4808** — DiT transformer fix (merged) ← this issue is a duplicate of this PR
- **#4810** — AR-side loaders fix (merged)
- **#4809** — parent tracking issue for all removed-API call sites
- **#4806** — original Hunyuan-image FP8 serving failure report
- Upstream vLLM [#43167](https://github.com/vllm-project/vllm/pull/43167) — removed `get_cache_scale` in v0.23.0

**Disposition:** duplicate-of-#4808

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
