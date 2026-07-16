# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

This is a **deploy-config mismatch**, not a model bug. You're running the **base** checkpoint (`tencent/HunyuanImage-3.0`) with the **Instruct** deploy config (`hunyuan_image_3_moe.yaml`).

The crash happens in `HunyuanImage3ForConditionalGeneration.__init__` at:

```python
# vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py, lines ~1561-1563
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # ← None + 1 → TypeError
```

**Why:** The base model's tokenizer only has 33 ratio tokens (`<img_ratio_0>` through `<img_ratio_32>`). The Instruct model adds 4 extra ratio tokens (`<img_ratio_33>` through `<img_ratio_36>`) for the additional VAE resolution bins used in the IT2I/T2I generation pipeline. `convert_tokens_to_ids` returns `None` for tokens not in the vocabulary, and `None + 1` crashes.

The `hunyuan_image_3_moe.yaml` config sets `pipeline: hunyuan_image_3_moe`, which forces the two-stage Instruct topology (AR token generation → MoE DiT). The base model does not have an AR stage and should use the single-stage DiT-only config.

This was noted during PR #2713 which consolidated the deploy configs — the old stage config had `modes` filtering that would have prevented the AR stage from loading for the base model, but the new deploy-level config forces the full Instruct topology.

## Immediate Fix (Workaround)

Use `hunyuan_image3_dit.yaml` for the base model:

```shell
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This has been confirmed to work by @FayeSpica.

For the **Instruct** model (`tencent/HunyuanImage-3.0-Instruct`), keep using:

```shell
vllm serve tencent/HunyuanImage-3.0-Instruct --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml \
  --trust-remote-code
```

## Config Reference

| Model | Deploy Config | Pipeline |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | Two-stage AR→MoE DiT |

## Proposed Code Improvement

A guard should be added in `__init__` to fail fast with a clear error message when the tokenizer doesn't have the required extended ratio tokens, instead of crashing with an opaque `TypeError`. Tencent's reference code guards against this at:

https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613

A separate issue should be opened to track this improvement (per @Gaohan123's request).

## draft_answer

## Root Cause

This is a **deploy-config mismatch**, not a model bug. You're running the **base** checkpoint (`tencent/HunyuanImage-3.0`) with the **Instruct** deploy config (`hunyuan_image_3_moe.yaml`).

The crash happens in `HunyuanImage3ForConditionalGeneration.__init__` at:

```python
# vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py, lines ~1561-1563
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # ← None + 1 → TypeError
```

**Why:** The base model's tokenizer only has 33 ratio tokens (`<img_ratio_0>` through `<img_ratio_32>`). The Instruct model adds 4 extra ratio tokens (`<img_ratio_33>` through `<img_ratio_36>`) for the additional VAE resolution bins used in the IT2I/T2I generation pipeline. `convert_tokens_to_ids` returns `None` for tokens not in the vocabulary, and `None + 1` crashes.

The `hunyuan_image_3_moe.yaml` config sets `pipeline: hunyuan_image_3_moe`, which forces the two-stage Instruct topology (AR token generation → MoE DiT). The base model does not have an AR stage and should use the single-stage DiT-only config.

This was noted during PR #2713 which consolidated the deploy configs — the old stage config had `modes` filtering that would have prevented the AR stage from loading for the base model, but the new deploy-level config forces the full Instruct topology.

## Immediate Fix (Workaround)

Use `hunyuan_image3_dit.yaml` for the base model:

```shell
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This has been confirmed to work by @FayeSpica.

For the **Instruct** model (`tencent/HunyuanImage-3.0-Instruct`), keep using:

```shell
vllm serve tencent/HunyuanImage-3.0-Instruct --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml \
  --trust-remote-code
```

## Config Reference

| Model | Deploy Config | Pipeline |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | Two-stage AR→MoE DiT |

## Proposed Code Improvement

A guard should be added in `__init__` to fail fast with a clear error message when the tokenizer doesn't have the required extended ratio tokens, instead of crashing with an opaque `TypeError`. Tencent's reference code guards against this at:

https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613

A separate issue should be opened to track this improvement (per @Gaohan123's request).

---

## Step diagnostics

### fetch

### draft
- **status**: success
- **summary**: The crash is a config mismatch: the base model `tencent/HunyuanImage-3.0` was started with the Instruct deploy config `hunyuan_image_3_moe.yaml` (two-stage AR→DiT MoE topology). The model's `__init__` unconditionally looks up extended ratio tokens `<img_ratio_33>` through `<img_ratio_36>` which only exist in the Instruct tokenizer. The immediate fix is to use `hunyuan_image3_dit.yaml` (single-stage DiT); a code guard to fail with a clear message is the proper long-term fix.
- **findings**: ['Root cause: `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py` lines 1561-1563 in `HunyuanImage3ForConditionalGeneration.__init__` unconditionally calls `tokenizer.convert_tokens_to_ids("<img_ratio_36>")` which returns `None` for the base tokenizer, then `ratio_36 + 1` raises `TypeError: unsupported operand type(s) for +: \'NoneType\' and \'int\'`', 'Mechanism: The base checkpoint (`tencent/HunyuanImage-3.0`) only has ratio tokens `<img_ratio_0>` through `<img_ratio_32>` (33 tokens). The Instruct checkpoint (`tencent/HunyuanImage-3.0-Instruct`) adds 4 extra ratio tokens (`<img_ratio_33>` through `<img_ratio_36>`) for the `HUNYUAN_IMAGE3_EXTRA_RESOLUTIONS` extra resolution bins used in the MoE-based IT2I/T2I pipeline', 'Config mismatch: `hunyuan_image_3_moe.yaml` sets `pipeline: hunyuan_image_3_moe` which forces the two-stage Instruct topology (AR stage with tokenizer ownership + MoE DiT stage). The base model should use `hunyuan_image3_dit.yaml` which sets `pipeline: hunyuan_image3_dit` (single-stage DiT-only)', 'PR #2713 (merged) consolidated configs and removed the old `hunyuan_image3_moe.yaml` from stage_configs in favor of the deploy-level config, making the two-stage Instruct topology the default path through that config file. The old config had `modes` filtering that would have prevented the AR stage from loading for the base model', 'Workaround confirmed by @FayeSpica: `vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code` runs successfully', 'Same issue would also affect `_get_prompt_updates` in `HunyuanImage3MultiModalProcessor` at inference time if the base model were somehow loaded through the AR path, because it looks up `<img_ratio_{_ratio_index}>` which can be 33-36 for extra resolutions']
- **files_read**: ['/rebase/vllm-omni/vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py', '/rebase/vllm-omni/vllm_omni/deploy/hunyuan_image_3_moe.yaml', '/rebase/vllm-omni/vllm_omni/deploy/hunyuan_image3_dit.yaml']
- **files_modified**: []
- **tests_requested**: ['Verify base model starts with `--deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml`', 'Verify Instruct model starts with `--deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml`']
- **tests_run**: []
- **assumptions**: ["The reporter's base model checkpoint at `tencent/HunyuanImage-3.0` has the same tokenizer as the official HF release (33 ratio tokens)", 'The reporter has access to NPU hardware (Kunpeng 920 / Ascend) as indicated by the environment info']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: Post the answer as a comment on issue #4827. The maintainer @Gaohan123 requested opening a new issue for tracking the guard improvement — that should be done separately.
- **answer_draft**: ## Root Cause

This is a **deploy-config mismatch**, not a model bug. You're running the **base** checkpoint (`tencent/HunyuanImage-3.0`) with the **Instruct** deploy config (`hunyuan_image_3_moe.yaml`).

The crash happens in `HunyuanImage3ForConditionalGeneration.__init__` at:

```python
# vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py, lines ~1561-1563
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # ← None + 1 → TypeError
```

**Why:** The base model's tokenizer only has 33 ratio tokens (`<img_ratio_0>` through `<img_ratio_32>`). The Instruct model adds 4 extra ratio tokens (`<img_ratio_33>` through `<img_ratio_36>`) for the additional VAE resolution bins used in the IT2I/T2I generation pipeline. `convert_tokens_to_ids` returns `None` for tokens not in the vocabulary, and `None + 1` crashes.

The `hunyuan_image_3_moe.yaml` config sets `pipeline: hunyuan_image_3_moe`, which forces the two-stage Instruct topology (AR token generation → MoE DiT). The base model does not have an AR stage and should use the single-stage DiT-only config.

This was noted during PR #2713 which consolidated the deploy configs — the old stage config had `modes` filtering that would have prevented the AR stage from loading for the base model, but the new deploy-level config forces the full Instruct topology.

## Immediate Fix (Workaround)

Use `hunyuan_image3_dit.yaml` for the base model:

```shell
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This has been confirmed to work by @FayeSpica.

For the **Instruct** model (`tencent/HunyuanImage-3.0-Instruct`), keep using:

```shell
vllm serve tencent/HunyuanImage-3.0-Instruct --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml \
  --trust-remote-code
```

## Config Reference
