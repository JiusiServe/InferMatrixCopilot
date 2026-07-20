# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:~line 1569 in HunyuanImage3ForConditionalGeneration.__init__ — `tokenizer.convert_tokens_to_ids("<img_ratio_36>")` returns None for the Base model's tokenizer, then `ratio_36 + 1` raises TypeError. Triggered by using hunyuan_image_3_moe.yaml (Instruct two-stage pipeline) with the Base model which lacks extended ratio tokens.

### Fix
Use `hunyuan_image3_dit.yaml` for the Base model: `vllm serve tencent/HunyuanImage-3.0 --omni --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code`

### Preconditions
None — the correct config is sufficient.

### Verification
Run the serve command with hunyuan_image3_dit.yaml as confirmed by the reporter: `vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code`

### Prevention
Add a guard in HunyuanImage3ForConditionalGeneration.__init__ that checks if ratio_36 (or ratio_33) is None and raises a clear ValueError like 'Base model (HunyuanImage-3.0) does not support the MoE/Instruct pipeline. Use hunyuan_image3_dit.yaml instead.' This prevents the opaque TypeError. Also update docs to clarify the config-to-model mapping.

### Disposition
keep-open — maintainer requested a separate issue for the code improvement (guard + docs); this issue documents the user-facing bug and workaround.

### Additional context
Hi! This is a **config mismatch** — the Base model `tencent/HunyuanImage-3.0` should not be used with `hunyuan_image_3_moe.yaml`, which is designed for the **Instruct** model (`tencent/HunyuanImage-3.0-Instruct`).

### Root cause

`hunyuan_image_3_moe.yaml` defines a two-stage pipeline (AR → Diffusion). The AR stage initializes `HunyuanImage3ForConditionalGeneration`, which looks up extended ratio tokens:

```python
# vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # ← crashes here
```

The Base model's tokenizer doesn't have `<img_ratio_36>`, so `convert_tokens_to_ids` returns `None`, and `None + 1` raises `TypeError`.

### Fix

Use `hunyuan_image3_dit.yaml` (single-stage DiT) for the Base model:

```shell
vllm serve tencent/HunyuanImage-3.0 \
  --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

The Instruct model should continue to use `hunyuan_image_3_moe.yaml`.

### Config reference

| Model | Deploy config | Pipeline |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | Two-stage AR → DiT |

A follow-up improvement has been requested to add a guard that fails fast with a clear error message when the Base model is loaded with the MoE/Instruct config.
