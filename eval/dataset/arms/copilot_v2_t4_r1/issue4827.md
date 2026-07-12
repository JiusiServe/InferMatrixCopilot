# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1560-1563` — `HunyuanImage3ForConditionalGeneration.__init__` unconditionally looks up Instruct-only ratio tokens in the tokenizer:

```python
self._end_ratio_id = tokenizer.convert_tokens_to_ids("<img_ratio_32>")
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # 💥 None + 1
```

The **Base** model (`tencent/HunyuanImage-3.0`) tokenizer only has ratio tokens 0–32. The extended tokens `<img_ratio_33>` through `<img_ratio_36>` exist only in the **Instruct** tokenizer (`tencent/HunyuanImage-3.0-Instruct`). When `convert_tokens_to_ids` can't find `<img_ratio_36>`, it returns `None`, and `None + 1` raises `TypeError`.

## Why This Happens

PR [#2713](https://github.com/vllm-project/vllm-omni/pull/2713) replaced the old `hunyuan_image_3_moe.yaml` which had a `modes` field that could filter out the AR stage for the Base model. The new config **always** forces the two-stage Instruct topology (AR → Diffusion). Running `--deploy-config hunyuan_image_3_moe.yaml` with the Base model now unconditionally initializes the AR stage, which in turn instantiates `HunyuanImage3ForConditionalGeneration` and hits this crash.

## Workaround (Confirmed)

Use the single-stage DiT-only config for the Base model:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This was confirmed working by @FayeSpica (see [comment](https://github.com/vllm-project/vllm-omni/issues/4827#issuecomment-...)).

## Deploy Config Map

| Model | Deploy Config | Pipeline |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT |
| `tencent/HunyuanImage-3.0-Instruct` (Instruct) | `hunyuan_image_3_moe.yaml` | Two-stage AR→DiT |

## Proposed Code Fix

Add a guard in `HunyuanImage3ForConditionalGeneration.__init__` (around line 1563):

```python
if ratio_33 is None or ratio_36 is None:
    raise ValueError(
        "Extended ratio tokens (<img_ratio_33>..<img_ratio_36>) not found in tokenizer. "
        "You are likely loading the Base model (tencent/HunyuanImage-3.0) with the "
        "Instruct deploy config (hunyuan_image_3_moe.yaml). "
        "Use hunyuan_image3_dit.yaml for the Base model instead."
    )
```

This mirrors the pattern in Tencent's reference code which guards on `model_version == "HunyuanImage-3.0"` ([ref](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613)).

## Disposition

Closing as resolved with a confirmed workaround. Per @Gaohan123's [request](https://github.com/vllm-project/vllm-omni/issues/4827#issuecomment-...), please open a separate issue to track the code-guard improvement if one hasn't been filed yet.

**Disposition:** close
