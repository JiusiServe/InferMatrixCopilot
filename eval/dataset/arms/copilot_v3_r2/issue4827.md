# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1561-1563 — HunyuanImage3ForConditionalGeneration.__init__ unconditionally calls tokenizer.convert_tokens_to_ids("<img_ratio_36>") which returns None for the Base checkpoint (these tokens only exist in Instruct); the result is used in arithmetic (ratio_36 + 1) causing TypeError. The root behavioral change is PR #2713, which removed modes-based filtering and forces the two-stage Instruct topology regardless of checkpoint.

### Fix
Add a guard after the ratio token lookups: if any of ratio_33..ratio_36 is None, raise a descriptive ValueError with the correct deploy config name. Also consider checking hf_config.model_version or the tokenizer vocab to short-circuit before reaching this code path.

### Workaround
Use --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml instead of hunyuan_image_3_moe.yaml for the Base model (tencent/HunyuanImage-3.0).

### Preconditions
The Base checkpoint (tencent/HunyuanImage-3.0) must be available locally; the dit config requires sufficient GPU memory for the DiT-only pipeline as configured in hunyuan_image3_dit.yaml (e.g., 4×NPU or GPU per the platform overlay).

### Verification
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code

### Prevention
Document the config↔checkpoint mapping in deploy/README or a docstring near the config files. Add a fail-fast guard in HunyuanImage3ForConditionalGeneration.__init__ that checks ratio_33..ratio_36 for None and suggests the correct config.

### Disposition
keep-open

### Additional context
## Root cause

You're running `tencent/HunyuanImage-3.0` (the **Base** checkpoint) with `--deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml`, which is the **Instruct** two-stage topology (AR → Diffusion).

The MoE config forces an AR stage that, during `HunyuanImage3ForConditionalGeneration.__init__`, tries to look up Instruct-only ratio tokens:

```python
# vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1561-1569
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")  # → None for Base
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # 💥 TypeError: NoneType + int
```

The Base tokenizer doesn't have `<img_ratio_33>`..`<img_ratio_36>` — those are Instruct-only tokens. Tencent's reference code guards this with a `model_version == "HunyuanImage-3.0"` check ([source](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613)).

This regression was introduced in [#2713](https://github.com/vllm-project/vllm-omni/pull/2713), which changed the deploy configs to force the two-stage topology instead of filtering by `modes`.

## Workaround (confirmed ✅)

Use the single-stage DiT config instead:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

@FayeSpica confirmed this works.

## Config selection guide

| Checkpoint | Deploy Config |
|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` |

## Proposed improvements (tracked separately)

1. **Fail-fast guard**: If `ratio_36 is None` (or any of these tokens are missing), raise a clear error like `"Base checkpoint detected; use hunyuan_image3_dit.yaml instead of hunyuan_image_3_moe.yaml"`.
2. **Docs**: Clarify the config↔checkpoint mapping in the README/deploy docs.

Per @Gaohan123's [request](https://github.com/vllm-project/vllm-omni/issues/4827#issuecomment-...), please open a new issue to track these improvements.

## Verification

```bash
# Should serve without crashing:
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```
