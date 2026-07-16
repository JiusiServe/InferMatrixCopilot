# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

This is already fixed on `main` — you're hitting a stale checkout.

**Root cause**: vLLM removed `QuantizationConfig.get_cache_scale` in v0.23.0 (vllm#43167). The HunyuanImage3 DiT transformer's `load_weights` at line 2238 of `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` was still calling it manually, and PR #4810 (AR-side fix) missed this site.

**Fix**: PR #4808 dropped the redundant manual branch. KV-cache scale names are now remapped exclusively through `maybe_remap_kv_scale_name(name, params_dict)` (line 2343), which was already present in the loader. This mirrors the approach taken for the AR loader in #4810.

Both PRs are merged:
- **#4808** — DiT loader fix (the one reported here)
- **#4810** — AR loader fix + regression tests for all 5 affected call sites

**What you need to do**: Update to current `main`. If you're pinned to an older commit, cherry-pick #4808.

Duplicate of #4809 / resolved by #4808.

**Disposition:** duplicate-of-4809

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
