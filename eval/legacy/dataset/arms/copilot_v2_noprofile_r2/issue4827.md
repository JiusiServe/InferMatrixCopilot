# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root cause

`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py` in `HunyuanImage3ForConditionalGeneration.__init__`:

```python
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # ← crashes: None + 1
```

The base model `tencent/HunyuanImage-3.0` tokenizer only defines ratio tokens `<img_ratio_0>` through `<img_ratio_32>`. Tokens `<img_ratio_33>`–`<img_ratio_36>` are **Instruct-only additions** (see Tencent's reference code guard at [tokenization_hunyuan_image_3.py#L613](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613)).

## Why it happens

The deploy config `hunyuan_image_3_moe.yaml` (pipeline: `hunyuan_image_3_moe`) is the **Instruct** two-stage topology (AR stage 0 → DiT stage 1). When you point it at the base checkpoint, the AR stage loads the base tokenizer — which lacks the extended ratio tokens — and the unconditional `convert_tokens_to_ids` → `None` → `None + 1` crashes model init.

## Workaround (confirmed by @FayeSpica)

Use the single-stage DiT config instead:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

## Config summary

| Deploy config | Pipeline | Model | Stages |
|---|---|---|---|
| `hunyuan_image3_dit.yaml` | `hunyuan_image3_dit` | Base (T2I DiT-only) | 1 (DiT) |
| `hunyuan_image_3_moe.yaml` | `hunyuan_image_3_moe` | Instruct (IT2I/T2I) | 2 (AR + DiT) |
| `hunyuan_image3_ar.yaml` | `hunyuan_image3_ar` | Instruct (AR-only) | 1 (AR) |

## Proposed fix

Add a guard in `HunyuanImage3ForConditionalGeneration.__init__` that checks the tokenizer actually has the extended tokens, and raises a clear error:

```python
if ratio_33 is None or ratio_36 is None:
    raise ValueError(
        "The tokenizer for this checkpoint lacks extended ratio tokens "
        "(<img_ratio_33>–<img_ratio_36>) required by the Instruct/MoE "
        "pipeline. Use hunyuan_image3_dit.yaml for the Base model."
    )
```

@Gaohan123 asked to track this improvement in a separate issue — please open one if you'd like to pursue the guard.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
