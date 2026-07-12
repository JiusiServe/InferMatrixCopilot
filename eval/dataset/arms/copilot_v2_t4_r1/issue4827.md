# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

The crash is a **deploy-config mismatch**: you passed `--deploy-config hunyuan_image_3_moe.yaml` with the **Base** checkpoint (`tencent/HunyuanImage-3.0`), but that config forces the two-stage AR→Diffusion **Instruct** topology.

During the AR-stage model init, the code tries to resolve Instruct-only special tokens that don't exist in the Base tokenizer:

```python
# hunyuan_image3.py:1562-1563 (HunyuanImage3ForConditionalGeneration.__init__)
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")  # → None (Base tokenizer lacks this)
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]           # → TypeError: None + 1
```

The Base tokenizer has ratio tokens `<img_ratio_0>` through `<img_ratio_32>` (33 buckets). The extended range `<img_ratio_33>`–`<img_ratio_36>` (4 extra buckets) exists **only** in the Instruct tokenizer. Tencent's reference `tokenization_hunyuan_image_3.py:613` guards this with an explicit `model_version == "HunyuanImage-3.0"` check.

## Workaround (use now)

Use the single-stage DiT deploy config instead:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This runs the Base model as a diffusion-only pipeline (no AR stage), which is the correct topology for the non-Instruct checkpoint. Confirmed working by @FayeSpica.

## Config guidance

| Model | Deploy Config | Pipeline |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | `hunyuan_image3_dit` (DiT-only) |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | `hunyuan_image_3_moe` (AR + DiT) |

## Improvement (tracked separately)

@akshatvishu suggested adding a guard in `HunyuanImage3ForConditionalGeneration.__init__` that checks whether the extended ratio tokens resolve in the tokenizer, and fails fast with a clear error message directing users to the correct config. @Gaohan123 asked to open a new issue to track this — please do so (or I can open one).

## Verification

1. Run the workaround command above — the server should start without the TypeError crash
2. The model should serve and generate images via the DiT-only pipeline

**Disposition:** close
