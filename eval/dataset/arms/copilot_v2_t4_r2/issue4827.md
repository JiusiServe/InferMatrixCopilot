# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

In `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py`, the `HunyuanImage3ForConditionalGeneration.__init__` unconditionally looks up extended ratio tokens that only exist in the **Instruct** tokenizer:

```python
# hunyuan_image3.py:1559-1563
self._start_ratio_id = tokenizer.convert_tokens_to_ids("<img_ratio_0>")
self._end_ratio_id = tokenizer.convert_tokens_to_ids("<img_ratio_32>")
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # 💥 NoneType + int
```

The **Base** model (`tencent/HunyuanImage-3.0`) tokenizer only has ratio tokens 0‑32. `convert_tokens_to_ids` returns `None` for `<img_ratio_33>` and `<img_ratio_36>`, and `None + 1` raises `TypeError`.

Tencent's reference code guards against this by checking the model version:
- <https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613>

## Why This Config Triggers It

The `vllm_omni/deploy/hunyuan_image_3_moe.yaml` config forces a **two-stage** AR → DiT topology (`pipeline: hunyuan_image_3_moe`). Stage 0 (AR) instantiates the full model `__init__`, which hits the crash. PR #2713 replaced the old config that had `modes` filtering to skip the AR stage for Base models.

## Workaround (Immediate)

Use the single-stage DiT config instead:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

Confirmed working by @FayeSpica.

## Proper Fix (Needs New Issue)

Add a None guard for `ratio_33` and `ratio_36` before computing `_ratio_other_slices`, or raise a clear error if someone tries to use the MoE/Instruct config with a Base checkpoint. @Gaohan123 requested opening a separate issue to track this improvement.

## Deploy Config Guide

| Model | Config | Pipeline |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | DiT only |
| `tencent/HunyuanImage-3.0-Instruct` (AR+DiT) | `hunyuan_image_3_moe.yaml` | AR → DiT |
| `tencent/HunyuanImage-3.0-Instruct` (AR only) | `hunyuan_image3_ar.yaml` | AR only |

**Disposition:** keep-open
