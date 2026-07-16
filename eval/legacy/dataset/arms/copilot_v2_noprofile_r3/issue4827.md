# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Diagnosis

This is a **config–model mismatch**, not a code bug in the model implementation itself.

### Root cause

`hunyuan_image3.py:1561-1563`:

```python
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")  # → None for Base
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]           # 💥 None + 1
```

The **base** model's tokenizer (`tencent/HunyuanImage-3.0`) only has ratio tokens 0–32. The **Instruct** model (`tencent/HunyuanImage-3.0-Instruct`) extends the vocabulary with `<img_ratio_33>` through `<img_ratio_36>` for the IT2I (image editing) pathway. When `convert_tokens_to_ids` doesn't find the token, it returns `None`, and the arithmetic crashes.

### Why the wrong config was selected

`hunyuan_image_3_moe.yaml` is a **two-stage AR→DiT pipeline** (stage 0 = autoregressive token generation, stage 1 = diffusion). It was added in [#2713](https://github.com/vllm-project/vllm-omni/pull/2713) for the Instruct variant. The AR stage owns the tokenizer and expects the extended vocabulary. Running the base model forces the two-stage topology to initialize the AR path, which hits the missing token.

Tencent's reference code guards against this by checking `model_version == "HunyuanImage-3.0"` — see [tokenization_hunyuan_image_3.py:613](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613).

## Workaround (use now)

Use the **single-stage DiT-only config** for the base model:

```bash
vllm serve tencent/HunyuanImage-3.0 \
  --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This was confirmed working by @FayeSpica.

### Config mapping summary

| Model | Deploy Config | Topology |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | Two-stage AR → DiT |

## Proper fix (tracking needed)

Two improvements proposed by @akshatvishu:

1. **Guard**: In `HunyuanImage3ForConditionalGeneration.__init__`, after looking up the ratio tokens, fail fast with a clear error if any return `None` — e.g.:
   ```python
   if ratio_36 is None:
       raise ValueError(
           "Token '<img_ratio_36>' not found in tokenizer. "
           "This config is for HunyuanImage-3.0-Instruct; "
           "use hunyuan_image3_dit.yaml for the Base model."
       )
   ```

2. **Docs**: Clarify the config-to-variant mapping in the README / deploy config comments.

@Gaohan123 has asked to track this in a **new issue** — please open one referencing this thread.

## Verification

After switching to `hunyuan_image3_dit.yaml`, the server should start without the `TypeError` and be ready to accept generation requests.

**Disposition:** keep-open

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
