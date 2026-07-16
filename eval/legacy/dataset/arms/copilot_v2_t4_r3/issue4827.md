# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

## Root Cause

The crash is a **deploy-config / model-checkpoint mismatch**, not a code bug in the model itself.

`hunyuan_image_3_moe.yaml` deploys the **two-stage Instruct topology** (AR stage 0 → DiT stage 1). The AR stage init in `HunyuanImage3ForConditionalGeneration.__init__` looks up extended ratio tokens:

**`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1561–1563`**
```python
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # ← crashes: None + 1
```

The **base** model (`tencent/HunyuanImage-3.0`) tokenizer only has `<img_ratio_0>` through `<img_ratio_32>`. The extended tokens `<img_ratio_33>`–`<img_ratio_36>` exist only in the **Instruct** tokenizer. When `convert_tokens_to_ids` returns `None`, the `None + 1` expression raises `TypeError`.

This logic was introduced in **PR #2713** (Feat/Add HunyuanImage-3.0-Instruct AR support), which added the `_ratio_other_slices` for the Instruct model's stage-transition logits processors. The upstream Tencent reference code guards against this in `tokenization_hunyuan_image_3.py:613` by checking `model_version == "HunyuanImage-3.0"` before accessing the extended ratio tokens — no equivalent guard exists in vllm-omni yet.

## Fix (Immediate Workaround)

Use the **DiT-only deploy config** for the base model:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This config (`pipeline: hunyuan_image3_dit`) deploys a single diffusion stage — no AR stage, no ratio-token lookups. Contributor @FayeSpica confirmed this works on NPU hardware.

## Config Reference

| Model | Deploy Config | Topology |
|-------|--------------|----------|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | Two-stage AR → DiT |
| `tencent/HunyuanImage-3.0-Instruct` (I2T) | `hunyuan_image3_i2t.yaml` | Single-stage AR |
| `tencent/HunyuanImage-3.0-Instruct` (T2T) | `hunyuan_image3_t2t.yaml` | Single-stage AR |

## Improvement (Separate Tracking)

A code guard should be added at the crash site to fail fast with a clear error message (e.g., "Base model requires `hunyuan_image3_dit.yaml`; `hunyuan_image_3_moe.yaml` is for Instruct only"). Per @Gaohan123's request, please open a **new issue** to track this improvement.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (

(promote with SkillStore.promote(name); candidates are never auto-activated)
