# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

## Root Cause

`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1561-1563`

```python
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # Crash: None + 1
```

The **Base** model (`tencent/HunyuanImage-3.0`) tokenizer does **not** include the extended ratio tokens `<img_ratio_33>` through `<img_ratio_36>`. Only the **Instruct** variant (`tencent/HunyuanImage-3.0-Instruct`) has them. When `convert_tokens_to_ids` can't find a token, it returns `None`, and the unconditional `ratio_36 + 1` raises `TypeError`.

## Why This Config?

You used `--deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml`. That config specifies `pipeline: hunyuan_image_3_moe` — a **two-stage** AR → DiT topology designed for the Instruct checkpoint. PR [#2713](https://github.com/vllm-project/vllm-omni/pull/2713) changed the old config to unconditionally force this two-stage path (the old config used a `modes` key that let the server skip the AR stage for Base checkpoints).

## Workaround (confirmed)

Use the single-stage DiT config for the Base model:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This was confirmed working by @FayeSpica [above](https://github.com/vllm-project/vllm-omni/issues/4827#issuecomment-...).

## Config Cheat Sheet

| Model | Deploy Config | Topology |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | Two-stage AR → DiT |
| `tencent/HunyuanImage-3.0-Instruct` (AR only) | `hunyuan_image3_ar.yaml` | Single-stage AR |

## Proper Fix

A guard should be added in `HunyuanImage3ForConditionalGeneration.__init__` to check whether the tokenizer actually contains the required ratio tokens, and fail fast with a clear error message (e.g., *"The tokenizer is missing extended ratio tokens. You may be loading the Base checkpoint with the Instruct/MoE config. Use `hunyuan_image3_dit.yaml` for the Base model."*). Tencent's reference code already does this at [`tokenization_hunyuan_image_3.py:613`](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613).

Per @Gaohan123's request, a separate issue will be opened to track this guard improvement.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
