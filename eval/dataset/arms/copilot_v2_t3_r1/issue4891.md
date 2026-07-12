# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

vLLM removed `QuantizationConfig.get_cache_scale()` in v0.23.0 (upstream PR [#43167](https://github.com/vllm-project/vllm/pull/43167)). vLLM-Omni's custom weight loaders were not updated to use the replacement `get_cache_scale_mapper()` path, causing quantized checkpoint loads to fail with:

```
AttributeError: 'ModelOptMixedPrecisionConfig' object has no attribute 'get_cache_scale'
```

## Fix Status — Already Merged

Both the AR side and the DiT (diffusion) side have been fixed:

- **PR [#4808](https://github.com/vllm-project/vllm-omni/pull/4808)** — Removed the dead `get_cache_scale` call from the **HunyuanImage3 DiT transformer** loader (`vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py`). KV-cache scale names are already remapped by the outer `AutoWeightsLoader` (in `pipeline_hunyuan_image3.py`) and by `maybe_remap_kv_scale_name` in the loader itself.
- **PR [#4810](https://github.com/vllm-project/vllm-omni/pull/4810)** — Fixed the four AR-side model-executor loaders (`hunyuan_image3.py`, `mammoth_moda2.py`, `mimo_audio_llm.py`, `qwen2_old.py`) to use `get_cache_scale_mapper()` or rely on `AutoWeightsLoader` delegation.

Both PRs have been merged. The current `main` branch contains **zero** calls to the removed API. A regression test (`tests/model_executor/models/test_kv_cache_scale_mapper.py`) ensures no future loader reintroduces it.

## Verification

```bash
# Confirm no production code calls the removed API
grep -r 'get_cache_scale(' vllm_omni/
# (should return nothing — only a comment reference remains)

# Run the regression test
pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py
```

## Workaround (if stuck on an older commit)

Cherry-pick PR #4808 (single-line removal) onto your branch, or update to the latest `main` which already includes both fixes.

## Related

- Parent tracking issue: [#4809](https://github.com/vllm-project/vllm-omni/issues/4809)
- Original Hunyuan-image FP8 serving report: [#4806](https://github.com/vllm-project/vllm-omni/issues/4806)

**Closing as resolved (fixed by #4808 + #4810).**

## draft_answer

## Root Cause

vLLM removed `QuantizationConfig.get_cache_scale()` in v0.23.0 (upstream PR [#43167](https://github.com/vllm-project/vllm/pull/43167)). vLLM-Omni's custom weight loaders were not updated to use the replacement `get_cache_scale_mapper()` path, causing quantized checkpoint loads to fail with:

```
AttributeError: 'ModelOptMixedPrecisionConfig' object has no attribute 'get_cache_scale'
```

## Fix Status — Already Merged

Both the AR side and the DiT (diffusion) side have been fixed:

- **PR [#4808](https://github.com/vllm-project/vllm-omni/pull/4808)** — Removed the dead `get_cache_scale` call from the **HunyuanImage3 DiT transformer** loader (`vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py`). KV-cache scale names are already remapped by the outer `AutoWeightsLoader` (in `pipeline_hunyuan_image3.py`) and by `maybe_remap_kv_scale_name` in the loader itself.
- **PR [#4810](https://github.com/vllm-project/vllm-omni/pull/4810)** — Fixed the four AR-side model-executor loaders (`hunyuan_image3.py`, `mammoth_moda2.py`, `mimo_audio_llm.py`, `qwen2_old.py`) to use `get_cache_scale_mapper()` or rely on `AutoWeightsLoader` delegation.

Both PRs have been merged. The current `main` branch contains **zero** calls to the removed API. A regression test (`tests/model_executor/models/test_kv_cache_scale_mapper.py`) ensures no future loader reintroduces it.

## Verification

```bash
# Confirm no production code calls the removed API
grep -r 'get_cache_scale(' vllm_omni/
# (should return nothing — only a comment reference remains)

# Run the regression test
pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py
```

## Workaround (if stuck on an older commit)

Cherry-pick PR #4808 (single-line removal) onto your branch, or update to the latest `main` which already includes both fixes.

## Related

- Parent tracking issue: [#4809](https://github.com/vllm-project/vllm-omni/issues/4809)
- Original Hunyuan-image FP8 serving report: [#4806](https://github.com/vllm-project/vllm-omni/issues/4806)

**Closing as resolved (fixed by #4808 + #4810).**

---

## Step diagnostics

### fetch

### draft
- **status**: success
- **summary**: Issue #4891 reports a legitimate bug — the HunyuanImage3 diffusion loader called the removed `QuantizationConfig.get_cache_scale` API — but both fixes covering this (PR #4808 for the DiT transformer and PR #4810 for the AR-side loaders) have already been merged into main. The current code contains no calls to `get_cache_scale`; the only remaining reference is a documentary comment at `hunyuan_image3_transformer.py:2238-2239`. A regression test (`tests/model_executor/models/test_kv_cache_scale_mapper.py`) now guards against reintroduction. This issue should be closed as resolved (it is effectively a duplicate of #4806/#4808).
- **findings**: ['The `load_weights` method in `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` previously called `quant_config.get_cache_scale(name)`, an API removed in vLLM v0.23.0 (upstream PR #43167).', 'PR #4808 (merged, CLOSED) removed the manual `get_cache_scale` branch from the DiT transformer loader — this is the exact fix the issue reporter described.', 'PR #4810 (merged) fixed the four AR-side loaders (`hunyuan_image3.py`, `mammoth_moda2.py`, `mimo_audio_llm.py`, `qwen2_old.py`) that also called the removed API.', 'A `grep` for `get_cache_scale(` across the entire `vllm_omni/` tree returns zero matches in production code — only the regression test and a comment remain.', 'The regression test `tests/model_executor/models/test_kv_cache_scale_mapper.py` (added in #4810) statically checks that none of the affected files contain `.get_cache_scale(` and validates both delegated and direct loader paths.']
- **files_read**: ['/rebase/vllm-omni/vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py', '/rebase/vllm-omni/tests/model_executor/models/test_kv_cache_scale_mapper.py']
- **files_modified**: []
- **tests_requested**: ['pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py']
- **tests_run**: []
- **assumptions**: ["The reporter's environment (vllm-omni main @ 86bdcaf3d, vLLM 0.24.0) predates the merge of PR #4808; the current checkout at /rebase/vllm-omni already includes both fixes.", 'The comment by akshatvishu identifying the issue as a duplicate of #4808 and pointing to #4809 is correct.']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: Close issue #4891 as resolved (duplicate of #4808/#4806). The fixes have been merged; recommend the reporter pull latest main or cherry-pick #4808 if stuck on an older commit.
- **answer_draft**: ## Root Cause

vLLM removed `QuantizationConfig.get_cache_scale()` in v0.23.0 (upstream PR [#43167](https://github.com/vllm-project/vllm/pull/43167)). vLLM-Omni's custom weight loaders were not updated to use the replacement `get_cache_scale_mapper()` path, causing quantized checkpoint loads to fail with:

```
AttributeError: 'ModelOptMixedPrecisionConfig' object has no attribute 'get_cache_scale'
```

## Fix Status — Already Merged

Both the AR side and the DiT (diffusion) side have been fixed:

- **PR [#4808](https://github.com/vllm-project/vllm-omni/pull/4808)** — Removed the dead `get_cache_scale` call from the **HunyuanImage3 DiT transformer** loader (`vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py`). KV-cache scale names are already remapped by the outer `AutoWeightsLoader` (in `pipeline_hunyuan_image3.py`) and by `maybe_remap_kv_scale_name` in the loader itself.
- **PR [#4810](https://github.com/vllm-project/vllm-omni/pull/4810)** — Fixed the four AR-side model-executor loaders (`hunyuan_image3.py`, `mammoth_moda2.py`, `mimo_audio_llm.py`, `qwen2_old.py`) to use `get_cache_scale_mapper()` or rely on `AutoWeightsLoader` delegation.

Both PRs have been merged. The current `main` branch contains **zero** calls to the removed API. A regression test (`tests/model_executor/models/test_kv_cache_scale_mapper.py`) ensures no future loader reintroduces it.

## Verification

```bash
# Confirm no production code calls the removed API
grep -r 'get_cache_scale(' vllm_omni/
# (should return nothing — only a comment reference remains)

# Run the regression test
pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py
```

## Workaround (if stuck on an older commit)

Cherry-pick PR #4808 (single-line removal) onto your branch, or update to the latest `main` which already includes both fixes.

## Related

- Parent tracking issue: [#4809](https://github.com/vllm-project/vllm-omni/issues/4809)
- Original Hunyuan-image FP8 serving report: [#480
