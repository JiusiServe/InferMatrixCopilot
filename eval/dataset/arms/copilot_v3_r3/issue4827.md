# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1562-1563`: `ratio_36 = tokenizer.convert_tokens_to_ids('<img_ratio_36>')` returns `None` for the base checkpoint because `<img_ratio_33>`…`<img_ratio_36>` are Instruct-only tokens. The subsequent `ratio_36 + 1` crashes with `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`. This path is reached because `hunyuan_image_3_moe.yaml` forces a two-stage AR+DiT pipeline that unconditionally calls the AR init code.

### Fix
Add a guard in `HunyuanImage3ForConditionalGeneration.__init__` (lines 1559-1566) to check whether `ratio_33` and `ratio_36` are `None` before computing `_ratio_other_slices`. If `None`, raise a `ValueError` explaining the config-model mismatch and pointing to `hunyuan_image3_dit.yaml`. Also add header comments to both deploy YAMLs documenting which checkpoint each serves.

### Workaround
Use `--deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml` instead of `hunyuan_image_3_moe.yaml` when serving the base checkpoint `tencent/HunyuanImage-3.0`.

### Preconditions
The base checkpoint `tencent/HunyuanImage-3.0` must be available in the HF cache. The `hunyuan_image3_dit.yaml` config is shipped in the same repo (verified present at `vllm_omni/deploy/hunyuan_image3_dit.yaml`). No special hardware beyond what DiT already requires.

### Verification
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code

### Prevention
Add a header block to `hunyuan_image_3_moe.yaml` and `hunyuan_image3_dit.yaml` stating the intended checkpoint (Instruct vs Base). Consider adding a pytest that instantiates the tokenizer for the base checkpoint and asserts that `convert_tokens_to_ids('<img_ratio_36>')` is `None` (to catch regressions that silently assume Instruct vocabulary).

### Disposition
keep-open — the workaround is confirmed and the root cause is diagnosed; the proper guard fix should land in a dedicated improvement PR (per @Gaohan123's request). Reopen condition: close once the guard PR is merged; re-open if the guard is removed without a replacement.

### Additional context
## Root Cause

You're loading the **base** checkpoint `tencent/HunyuanImage-3.0` with the **Instruct** deploy config `hunyuan_image_3_moe.yaml`. That config sets up a two-stage pipeline (`pipeline: hunyuan_image_3_moe`) which launches an AR (autoregressive) stage. During AR init, the code at:

**`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1562-1563`**
```python
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]
```

calls `convert_tokens_to_ids("<img_ratio_36>")`. The base model's tokenizer doesn't have `<img_ratio_33>` through `<img_ratio_36>` — those are **Instruct-only** tokens (IDs 130103–130106, see `prompt_utils.py:60`). So `ratio_36` is `None`, and `None + 1` raises `TypeError`.

This matches Tencent's reference implementation: [`tokenization_hunyuan_image_3.py:613`](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613) guards with `model_version == "HunyuanImage-3.0"`.

## Workaround (available now)

Use the **DiT-only** config for the base model:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This was confirmed working by @FayeSpica.

### Config mapping

| Checkpoint | Deploy Config | Pipes |
|---|---|---|
| `tencent/HunyuanImage-3.0` (base) | `hunyuan_image3_dit.yaml` | DiT only |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | AR → DiT (two-stage) |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image3_ar.yaml` | AR only |

## Proper Fix

Two items (tracked in a follow-up per @Gaohan123):

1. **Guard** — in `HunyuanImage3ForConditionalGeneration.__init__` around lines 1559-1566, check whether `ratio_33`/`ratio_36` are `None` and raise a clear `ValueError` like:
   > `"<img_ratio_33>–<img_ratio_36> not found in tokenizer. The base model requires 'hunyuan_image3_dit.yaml', not 'hunyuan_image_3_moe.yaml'."`

2. **Docs** — add a header comment to both deploy YAML files clarifying which checkpoint each targets.

## Verification

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

Should start without the `TypeError` and show the DiT stage loading.
