# Run report

- task: {'kind': 'pr_review', 'repo': 'vllm-omni', 'pr': 4810, 'issue': None, 'report_only': True, 'post': False, 'params': {}}

- checkout: PR-TIME TREE (head f9665cc223c8) — the tree matches the diff exactly; repo-wide greps DO reflect PR-time state

## review_text

**Validated:**
- [validated] hunyuan_image3.py:222-229 — removed `get_cache_scale` block; delegated loader correctly relies on outer AutoWeightsLoader mapper. The `maybe_remap_kv_scale_name` fallback in the else branch at ~line 240 is preserved and compatible.
- [validated] mammoth_moda2.py:486-489 — added `get_cache_scale_mapper().apply(weights)` with double None-guard (`quant_config is not None` → `cache_scale_mapper is not None`). All three branch combinations can occur and are handled correctly.
- [validated] mimo_audio_llm.py:1156-1159 — same pattern as mammoth_moda2. Double None-guard correct; `maybe_remap_kv_scale_name` fallback preserved.
- [validated] qwen2_old.py:338 — removed `getattr(self.quant_config, 'get_cache_scale', None)` guard and `get_cache_scale` block. Correct because Qwen2ForCausalLM uses AutoWeightsLoader(self) at line 444 which applies the mapper before delegating.
- [sweep] Grep for `.get_cache_scale(` repo-wide found only one remaining caller outside the PR's four files: `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py:2238`. This is in the diffusion pipeline path, not in model_executor.
- [sweep] All four files grep-clean for `.get_cache_scale(` after the diff — confirmed via `grep` against the four changed files, matching the test's `_STALE_API_FILES` assertions.
- [sweep] No rebase/merge damage: no duplicated code blocks, no dropped hunks, no references to moved or renamed symbols across all four files.
- [sweep] `maybe_remap_kv_scale_name` fallback preserved in all four files' else branches — the mapper renames `.k_proj.output_scale` → `.attn.k_scale`, and `maybe_remap_kv_scale_name` handles additional FP8 scale name remapping; these are complementary, not conflicting.

`vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py:2238` [major] — The PR removes `get_cache_scale` calls from four model-executor loaders but leaves `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` line 2238 unchanged. This file still calls `self.quant_config.get_cache_scale(name)`. If the upstream `QuantizationConfig` removes `get_cache_scale`, this will raise `AttributeError` at weight-load time for the HunyuanImage3 diffusion pipeline. Either migrate this loader to the new `get_cache_scale_mapper` pattern like the other loaders, or document why it is exempt and verify that the old API remains accessible. (evidence: grep for `\.get_cache_scale\(` across the repo shows only this line and the test assertion remain; the four executor files in the diff are clean. The test file's `_STALE_API_FILES` list does not include this path.)

`tests/model_executor/models/test_kv_cache_scale_mapper.py:14` [major] — The `_STALE_API_FILES` list in the test file (line 14) includes only the four model-executor files, but `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` also still calls `.get_cache_scale(` (see line 2238). The static grep test at line 84 therefore does not detect this remaining deprecated-call. Add the diffusion file path to `_STALE_API_FILES` so the test can catch future regressions. (evidence: Grep finds get_cache_scale at hunyuan_image3_transformer.py:2238; this file is absent from _STALE_API_FILES (lines 14-19).)

`tests/model_executor/models/test_kv_cache_scale_mapper.py:121` [minor] — The test `test_direct_custom_loaders_apply_cache_scale_mapper` (line 129) uses `_QuantConfigWithoutOldCacheScale` which always returns a non‑None mapper. The guard `if cache_scale_mapper is not None:` in mammoth_moda2.py:488 and mimo_audio_llm.py:1158 is therefore never exercised. Consider adding a parametrized case where `get_cache_scale_mapper()` returns None to ensure the guard correctly skips mapper application. (evidence: Read tests/model_executor/models/test_kv_cache_scale_mapper.py lines 121-148: `_QuantConfigWithoutOldCacheScale` always constructs and returns `_RecordingCacheScaleMapper()` from `get_cache_scale_mapper()`. No test variant supplies a quant config whose mapper is `None`.)

`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:225` [minor] — The comment at line 225 (added by this PR) refers to 'the outer AutoWeightsLoader' as the source of KV-cache scale renaming, but `HunyuanModel.load_weights` does not call `AutoWeightsLoader` or `get_cache_scale_mapper()` itself. The actual fallback is `maybe_remap_kv_scale_name` in the `else` clause. Clarify the comment to accurately describe the renaming path or name the outer caller if it exists, to avoid confusion. (evidence: Read hunyuan_image3.py HunyuanModel.load_weights — no AutoWeightsLoader import or usage; fallthrough path at ~line 306 calls `maybe_remap_kv_scale_name(name, params_dict)`. Grep for `AutoWeightsLoader` in hunyuan_image3/ directory returned no matches.)

`vllm_omni/model_executor/models/qwen2_5_omni/qwen2_old.py:338` [minor] — `Qwen2Model.load_weights` (line 338) no longer uses `get_cache_scale` but does not apply `cache_scale_mapper.apply(weights)`, relying instead on the outer `Qwen2ForCausalLM.load_weights` (which uses `AutoWeightsLoader`) to apply the mapper before delegation. This implicit dependency is easy to miss. Add a comment noting that the mapper is expected to be applied by the outer loader to make the contract explicit. (evidence: Read qwen2_old.py Qwen2Model.load_weights — no mapper call added. Read Qwen2ForCausalLM.load_weights at bottom of file — uses `AutoWeightsLoader(self, ...).load_weights(weights)` which internally applies `get_cache_scale_mapper`.)

**Verdict:** REQUEST CHANGES

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
