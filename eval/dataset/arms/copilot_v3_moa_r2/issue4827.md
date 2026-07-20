# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
hunyuan_image3.py:1562-1563 — `tokenizer.convert_tokens_to_ids("<img_ratio_36>")` returns `None` for the Base model tokenizer (which lacks extended ratio tokens), then `ratio_36 + 1` raises TypeError. The `hunyuan_image_3_moe.yaml` config forces the Instruct two-stage topology onto the Base checkpoint.

### Fix
Switch to `vllm_omni/deploy/hunyuan_image3_dit.yaml` when serving the Base model `tencent/HunyuanImage-3.0`.

### Workaround
N/A — the correct config is the fix.

### Preconditions
The Base model `tencent/HunyuanImage-3.0` must be available locally or downloadable. The `hunyuan_image3_dit.yaml` config requires 4 devices (GPU/NPU) for tensor parallelism.

### Verification
Run `vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code` and confirm the server starts without TypeError.

### Prevention
Add a guard in `HunyuanImage3ForConditionalGeneration.__init__` that raises a clear `ValueError` if extended ratio tokens (`<img_ratio_33>`, `<img_ratio_36>`) are missing from the tokenizer, with a message directing users to `hunyuan_image3_dit.yaml` for the Base model.

### Disposition
close — this is a user-config error (wrong YAML for the model variant); a follow-up code improvement issue was already requested by the maintainer.

### Additional context
## Root Cause

The crash happens because you are using `hunyuan_image_3_moe.yaml` with the **Base** model (`tencent/HunyuanImage-3.0`), but this deploy config is designed exclusively for the **Instruct** model (`tencent/HunyuanImage-3.0-Instruct`).

During `HunyuanImage3ForConditionalGeneration.__init__`, the code unconditionally looks up extended ratio tokens:

```python
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")  # → None for Base
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")  # → None for Base
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]          # TypeError: None + 1
```

The Base model's tokenizer doesn't contain `<img_ratio_33>` through `<img_ratio_36>`, so `convert_tokens_to_ids` returns `None`, and `None + 1` raises `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`.

## Fix

Use the correct deploy config for the Base model — the **single-stage DiT** config:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code
```

### Config overview

| Model | Deploy Config | Topology |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | Two-stage: AR → DiT MoE |
| Either (AR only) | `hunyuan_image3_ar.yaml` | Single-stage AR only |

## Future Improvement

The current code lacks a defensive guard — it would be cleaner to fail fast with a clear error message when a Base checkpoint is loaded with the Instruct config. This improvement was requested by the maintainer and can be tracked in a separate issue (see [#2713](https://github.com/vllm-project/vllm-omni/pull/2713) for context on how the config topology changed).
