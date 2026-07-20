# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
Base model tokenizer lacks `<img_ratio_36>` token; `tokenizer.convert_tokens_to_ids()` returns `None`; `None + 1` crashes at `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1563` (`self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]`).

### Fix
Use `vllm_omni/deploy/hunyuan_image3_dit.yaml` (single-stage DiT) instead of `vllm_omni/deploy/hunyuan_image_3_moe.yaml` (two-stage AR→DiT) when serving the Base model `tencent/HunyuanImage-3.0`.

### Workaround
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code

### Preconditions
Requires sufficient GPU hardware for HunyuanImage-3.0 inference (NPU or CUDA). The Base model must be downloaded and accessible.

### Verification
Run the corrected serve command and confirm workers start without TypeError.

### Prevention
Add a guard in `HunyuanImage3ForConditionalGeneration.__init__` to check if critical tokenizer tokens (like `<img_ratio_36>`) are present before using them, and raise a clear `ValueError` explaining the Base/Instruct config mismatch. Also document the Base vs Instruct config mapping in deploy YAML comments and docs. A separate tracking issue will be opened for this improvement.

### Disposition
close

### Additional context
## Root Cause

The crash is a **config mismatch** between the Base model and the Instruct deploy config.

`hunyuan_image_3_moe.yaml` is a **two-stage (AR → DiT) config** designed specifically for the **Instruct** model (`tencent/HunyuanImage-3.0-Instruct`). The Base model (`tencent/HunyuanImage-3.0`) has a smaller tokenizer vocabulary that does **not** include the extended ratio tokens `<img_ratio_33>` through `<img_ratio_36>`.

During `HunyuanImage3ForConditionalGeneration.__init__` (`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1561–1563`):

```python
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")  # → None for Base model
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # None + 1 → TypeError
```

The Base tokenizer returns `None` for `<img_ratio_36>`, and `None + 1` raises `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`.

## Fix

Use the correct deploy config for the Base model — **`hunyuan_image3_dit.yaml`** (single-stage DiT, no AR stage):

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code
```

## Config Reference

| Model | Deploy Config | Architecture |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT only |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | Two-stage: AR (stage 0) → DiT (stage 1) |
| Either model (AR standalone) | `hunyuan_image3_ar.yaml` | AR stage only |

## Verification

Run the corrected command; the server should start without the `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'` crash. Workers will load the model successfully.

## Prevention

A code-level guard is planned to fail fast with a clear error message if someone accidentally loads the Base model with the MoE/Instruct config. Tencent's [reference code](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613) already guards on `model_version == "HunyuanImage-3.0"` to skip the extended ratio tokens for the Base model. A separate tracking issue will be opened to implement this guard in vLLM-Omni.

## Disposition

**Close** – the immediate issue is resolved by using the correct deploy config. The future guard improvement will be tracked in a new issue.
