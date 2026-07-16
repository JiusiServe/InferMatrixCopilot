# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4891, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Status: Already fixed — duplicate of PR #4808

This bug was fixed in **[PR #4808](https://github.com/vllm-project/vllm-omni/pull/4808)** (merged), which removed the stale `get_cache_scale` call from the HunyuanImage3 DiT loader.

### Root cause

vLLM upstream removed `QuantizationConfig.get_cache_scale` in v0.23.0 ([vllm#43167](https://github.com/vllm-project/vllm/pull/43167)), replacing it with `get_cache_scale_mapper()`. PR #4810 migrated the 4 AR-side custom loaders, but the diffusion-side `HunyuanImage3Model.load_weights` in `hunyuan_image3_transformer.py` was missed and still called:

```python
# OLD code (removed by #4808):
scale_name = self.quant_config.get_cache_scale(name)
param = params_dict[scale_name]
weight_loader(param, loaded_weight[0])
```

This branch was redundant: the DiT is loaded through an outer `AutoWeightsLoader` that already remaps `.output_scale` → `.attn.{k,v,q}_scale`, and the same loader already calls `maybe_remap_kv_scale_name` on the fall-through path.

### Current state (verified)

On current main, the only reference at the reported crash site (line 2239) is a comment:

```python
# KV-cache scales are renamed via maybe_remap_kv_scale_name below;
# quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).
```

`grep -r 'get_cache_scale(' vllm_omni/diffusion/` returns zero matches.

### What you should do

1. **Pull latest main**: `git pull origin main` — your commit `86bdcaf3d` likely predates the merge of #4808.
2. **Verify the fix** with the regression test:
   ```bash
   pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py
   ```

### Related

- **PR #4808**: Removed the dead branch in the DiT loader (this bug)
- **PR #4810**: Migrated the 4 AR-side loaders + added `test_kv_cache_scale_mapper.py`
- **Issue #4809**: Parent tracking issue for all `get_cache_scale` call sites
- **Upstream vllm#43167**: Removed `get_cache_scale` in v0.23.0

## draft_answer

## Status: Already fixed — duplicate of PR #4808

This bug was fixed in **[PR #4808](https://github.com/vllm-project/vllm-omni/pull/4808)** (merged), which removed the stale `get_cache_scale` call from the HunyuanImage3 DiT loader.

### Root cause

vLLM upstream removed `QuantizationConfig.get_cache_scale` in v0.23.0 ([vllm#43167](https://github.com/vllm-project/vllm/pull/43167)), replacing it with `get_cache_scale_mapper()`. PR #4810 migrated the 4 AR-side custom loaders, but the diffusion-side `HunyuanImage3Model.load_weights` in `hunyuan_image3_transformer.py` was missed and still called:

```python
# OLD code (removed by #4808):
scale_name = self.quant_config.get_cache_scale(name)
param = params_dict[scale_name]
weight_loader(param, loaded_weight[0])
```

This branch was redundant: the DiT is loaded through an outer `AutoWeightsLoader` that already remaps `.output_scale` → `.attn.{k,v,q}_scale`, and the same loader already calls `maybe_remap_kv_scale_name` on the fall-through path.

### Current state (verified)

On current main, the only reference at the reported crash site (line 2239) is a comment:

```python
# KV-cache scales are renamed via maybe_remap_kv_scale_name below;
# quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).
```

`grep -r 'get_cache_scale(' vllm_omni/diffusion/` returns zero matches.

### What you should do

1. **Pull latest main**: `git pull origin main` — your commit `86bdcaf3d` likely predates the merge of #4808.
2. **Verify the fix** with the regression test:
   ```bash
   pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py
   ```

### Related

- **PR #4808**: Removed the dead branch in the DiT loader (this bug)
- **PR #4810**: Migrated the 4 AR-side loaders + added `test_kv_cache_scale_mapper.py`
- **Issue #4809**: Parent tracking issue for all `get_cache_scale` call sites
- **Upstream vllm#43167**: Removed `get_cache_scale` in v0.23.0

---

## Step diagnostics

### fetch

### draft
- **status**: success
- **summary**: The reported bug is already fixed on current main. PR #4808 removed the dead `get_cache_scale` call from the HunyuanImage3 diffusion loader (`hunyuan_image3_transformer.py`). The only remaining reference at that site is a comment (line 2239) documenting the removal. Grep confirms zero active calls to `.get_cache_scale(` in the entire `vllm_omni/diffusion/` tree. The reporter likely hit this on a slightly older main revision before #4808 merged.
- **findings**: ['Root cause: vLLM removed `QuantizationConfig.get_cache_scale` in v0.23.0 (vllm#43167). The HunyuanImage3 DiT loader (`hunyuan_image3_transformer.py`) still had a manual `get_cache_scale` branch that was missed when PR #4810 migrated the AR-side loaders.', 'Fix already merged: PR #4808 (CLOSED/MERGED) removed the redundant manual `get_cache_scale` branch from `HunyuanImage3Model.load_weights`. The DiT is loaded through an outer `AutoWeightsLoader` that already remaps KV-cache scale names, and the same loader calls `maybe_remap_kv_scale_name` on the fall-through path, so the manual branch was both dead and harmful.', 'Current code (verified): line 2239 of `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py` contains only a comment: `# quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).` No active `get_cache_scale(` call remains.', "Grep confirmation: `grep -r 'get_cache_scale(' vllm_omni/diffusion/` returns zero matches. The only `get_cache_scale` references in the whole `vllm_omni/` tree are (a) the comment above and (b) two uses of the new `get_cache_scale_mapper()` API in mammoth_moda2 and mimo_audio loaders.", 'PR #4810 (MERGED) fixed the AR-side loaders (hunyuan_image3 AR, mammoth_moda2, mimo_audio, qwen2_old) and added a regression test (`tests/model_executor/models/test_kv_cache_scale_mapper.py`) that enforces no stale `get_cache_scale` calls.']
- **files_read**: ['/rebase/vllm-omni/vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py', '/rebase/vllm-omni/tests/model_executor/models/test_kv_cache_scale_mapper.py']
- **files_modified**: []
- **tests_requested**: ['pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py']
- **tests_run**: []
- **assumptions**: ["The reporter's commit 86bdcaf3d may predate the merge of PR #4808; current tree has the fix."]
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: Close as duplicate of PR #4808. The reporter should `git pull` latest main to pick up the fix. For verification, run the regression test: `pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py`.
- **answer_draft**: ## Status: Already fixed — duplicate of PR #4808

This bug was fixed in **[PR #4808](https://github.com/vllm-project/vllm-omni/pull/4808)** (merged), which removed the stale `get_cache_scale` call from the HunyuanImage3 DiT loader.

### Root cause

vLLM upstream removed `QuantizationConfig.get_cache_scale` in v0.23.0 ([vllm#43167](https://github.com/vllm-project/vllm/pull/43167)), replacing it with `get_cache_scale_mapper()`. PR #4810 migrated the 4 AR-side custom loaders, but the diffusion-side `HunyuanImage3Model.load_weights` in `hunyuan_image3_transformer.py` was missed and still called:

```python
# OLD code (removed by #4808):
scale_name = self.quant_config.get_cache_scale(name)
param = params_dict[scale_name]
weight_loader(param, loaded_weight[0])
```

This branch was redundant: the DiT is loaded through an outer `AutoWeightsLoader` that already remaps `.output_scale` → `.attn.{k,v,q}_scale`, and the same loader already calls `maybe_remap_kv_scale_name` on the fall-through path.

### Current state (verified)

On current main, the only reference at the reported crash site (line 2239) is a comment:

```python
# KV-cache scales are renamed via maybe_remap_kv_scale_name below;
# quant_config.get_cache_scale was removed in vLLM v0.23.0 (see #4810).
```

`grep -r 'get_cache_scale(' vllm_omni/diffusion/` returns zero matches.

### What you should do

1. **Pull latest main**: `git pull origin main` — your commit `86bdcaf3d` likely predates the merge of #4808.
2. **Verify the fix** with the regression test:
   ```bash
   pytest -q tests/model_executor/models/test_kv_cache_scale_mapper.py
   ```

### Related

- **PR #4808**: Removed the dead branch in the DiT loader (this bug)
- **PR #4810**: Migrated the 4 AR-side loaders + added `test_kv_cache_scale_mapper.py`
- **Issue #4809**: Parent tracking issue for all `get_cache_scale` call sites
- **Upstream vllm#43167**: Removed `get_cache_scale` in v0.23.0
