# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1561-1563 — `ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")` returns `None` for the base tokenizer (which lacks ratio tokens 33–36), then `ratio_36 + 1` crashes with `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`. The user should use `hunyuan_image3_dit.yaml` (single-stage DiT) for the base model, not `hunyuan_image_3_moe.yaml` (two-stage Instruct).

### Fix
Use the correct deploy config: `--deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml` for `tencent/HunyuanImage-3.0` (base). Only use `hunyuan_image_3_moe.yaml` for `tencent/HunyuanImage-3.0-Instruct`.

### Workaround
`vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code`

### Preconditions
The base `tencent/HunyuanImage-3.0` checkpoint and its tokenizer (which has ratio tokens 0–32 but not 33–36) must be available locally in HF offline cache.

### Verification
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code

### Prevention
Add a guard in `HunyuanImage3ForConditionalGeneration.__init__()` (~line 1561) to check that `ratio_33` and `ratio_36` are not `None` before using them, and raise a clear `ValueError` explaining that the tokenizer lacks extended ratio tokens needed for the Instruct pipeline — suggesting the user either switch to the Instruct checkpoint or use `hunyuan_image3_dit.yaml`.

### Disposition
close

### Additional context
## Root Cause

The crash occurs because you ran the **base** `tencent/HunyuanImage-3.0` model with `--deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml`, which is designed for the **Instruct** variant (`tencent/HunyuanImage-3.0-Instruct`).

**File:** `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1561–1563`

```python
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # ← crashes: None + 1
```

The Instruct tokenizer has extended ratio tokens `<img_ratio_33>`–`<img_ratio_36>` for the larger resolution group used in the two-stage AR→DiT pipeline. The base model's tokenizer only has ratio tokens 0–32, so `convert_tokens_to_ids("<img_ratio_36>")` returns `None`, and `None + 1` raises `TypeError`.

This matches the pattern in Tencent's reference code where `tokenization_hunyuan_image_3.py:613` checks `model_version == "HunyuanImage-3.0"` before accessing these extended tokens.

## Fix (Immediate Workaround)

Use the **single-stage DiT config** for the base model:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

### Config Mapping

| Model | Correct Deploy Config | Topology |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | Two-stage AR→DiT |

## Prevention

A code guard should be added in `HunyuanImage3ForConditionalGeneration.__init__()` to fail fast with a clear error message when the tokenizer lacks the extended ratio tokens, rather than crashing with a cryptic `TypeError: NoneType + int`. This improvement is being tracked separately (per maintainer request).

## Verification

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

Server should start successfully and accept image generation requests.
