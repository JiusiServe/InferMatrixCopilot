# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

The `tencent/HunyuanImage-3.0` (Base) tokenizer does **not** contain the extended ratio tokens `<img_ratio_33>` through `<img_ratio_36>`. These tokens only exist in the `HunyuanImage-3.0-Instruct` tokenizer. When you use `--deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml` (the two-stage Instruct pipeline: AR → DiT), the AR stage init crashes at:

**`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1562-1563`**
```python
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")  # → None for Base
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]         # TypeError: None + int
```

The Base model's tokenizer has ratio tokens `<img_ratio_0>` through `<img_ratio_32>` (33 buckets). The Instruct tokenizer adds 4 more (`<img_ratio_33>` … `<img_ratio_36>`) for the extra resolution buckets used in the text+image-to-image (IT2I) pipeline.

This regression was introduced (or exposed) by PR [#2713](https://github.com/vllm-project/vllm-omni/pull/2713), which changed the config to force the two-stage Instruct topology instead of letting `modes` filter it out.

## Workaround (confirmed)

Use the **single-stage DiT config** for the Base model:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This was confirmed working by @FayeSpica in the thread.

## Config guide

| Model | Deploy config | Pipeline |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT only |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | Two-stage AR → DiT |

## Improvement needed

The code should **fail fast with a clear message** when someone accidentally uses the wrong config, rather than crashing with an opaque `TypeError: NoneType + int`. The fix would mirror Tencent's own guard in their reference code ([tokenization_hunyuan_image_3.py:L613](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613)) which checks `model_version == "HunyuanImage-3.0"` before accessing the extended tokens.

Per @Gaohan123's request, this improvement should be tracked in a **new issue** — please open one if you'd like to contribute the guard.

## Verification

After switching to `hunyuan_image3_dit.yaml`, the model should load without error and you should see the DiT stage initialize successfully (look for the VAE/ViT encoder load messages in the worker logs).

## draft_answer

## Root Cause

The `tencent/HunyuanImage-3.0` (Base) tokenizer does **not** contain the extended ratio tokens `<img_ratio_33>` through `<img_ratio_36>`. These tokens only exist in the `HunyuanImage-3.0-Instruct` tokenizer. When you use `--deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml` (the two-stage Instruct pipeline: AR → DiT), the AR stage init crashes at:

**`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1562-1563`**
```python
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")  # → None for Base
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]         # TypeError: None + int
```

The Base model's tokenizer has ratio tokens `<img_ratio_0>` through `<img_ratio_32>` (33 buckets). The Instruct tokenizer adds 4 more (`<img_ratio_33>` … `<img_ratio_36>`) for the extra resolution buckets used in the text+image-to-image (IT2I) pipeline.

This regression was introduced (or exposed) by PR [#2713](https://github.com/vllm-project/vllm-omni/pull/2713), which changed the config to force the two-stage Instruct topology instead of letting `modes` filter it out.

## Workaround (confirmed)

Use the **single-stage DiT config** for the Base model:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This was confirmed working by @FayeSpica in the thread.

## Config guide

| Model | Deploy config | Pipeline |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT only |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | Two-stage AR → DiT |

## Improvement needed

The code should **fail fast with a clear message** when someone accidentally uses the wrong config, rather than crashing with an opaque `TypeError: NoneType + int`. The fix would mirror Tencent's own guard in their reference code ([tokenization_hunyuan_image_3.py:L613](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613)) which checks `model_version == "HunyuanImage-3.0"` before accessing the extended tokens.

Per @Gaohan123's request, this improvement should be tracked in a **new issue** — please open one if you'd like to contribute the guard.

## Verification

After switching to `hunyuan_image3_dit.yaml`, the model should load without error and you should see the DiT stage initialize successfully (look for the VAE/ViT encoder load messages in the worker logs).

---

## Step diagnostics

### fetch

### draft
- **status**: success
- **summary**: The crash is a config mismatch: `hunyuan_image_3_moe.yaml` forces the two-stage Instruct topology (AR→DiT), but the Base model tokenizer lacks the extended ratio tokens `<img_ratio_33>` through `<img_ratio_36>` that only exist in the Instruct tokenizer. The AR-stage init at `hunyuan_image3.py:1562-1563` calls `tokenizer.convert_tokens_to_ids("<img_ratio_36>")` → `None`, then `None + 1` → `TypeError`. The workaround is to use `--deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml` for the Base model (confirmed working by @FayeSpica). A code guard is still needed to fail fast with a clear message.
- **findings**: ['Root cause at `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1562-1563`: `ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")` returns `None` for Base model, then `self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]` raises `TypeError: unsupported operand type(s) for +: \'NoneType\' and \'int\'`.', "Mechanism: Base model (`HunyuanImage-3.0`) tokenizer only has ratio tokens 0–32 (33 buckets). Instruct model (`HunyuanImage-3.0-Instruct`) adds `<img_ratio_33>` through `<img_ratio_36>` (4 extra resolution buckets for the two-stage AR→DiT pipeline). The MoE config's AR stage unconditionally references these tokens.", 'Config mismatch: `hunyuan_image_3_moe.yaml` declares `pipeline: hunyuan_image_3_moe` (two-stage AR+DiT) and is the Instruct config. `hunyuan_image3_dit.yaml` declares `pipeline: hunyuan_image3_dit` (single-stage DiT-only) and is the correct config for the Base model.', 'Prior change: PR #2713 changed the config to force the two-stage Instruct topology instead of letting `modes` filter, which is why the old config (before #2713) may have worked.', 'Workaround confirmed: @FayeSpica verified `vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code` works fine.', 'No guard exists: the code does not check whether `convert_tokens_to_ids` returned `None` before arithmetic; a fast-fail guard with a clear error message is needed.', 'Upstream reference: Tencent\'s reference code guards against this at https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613 by checking `model_version == "HunyuanImage-3.0"`.']
- **files_read**: ['/rebase/vllm-omni/vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py', '/rebase/vllm-omni/vllm_omni/deploy/hunyuan_image_3_moe.yaml', '/rebase/vllm-omni/vllm_omni/deploy/hunyuan_image3_dit.yaml']
- **files_modified**: []
- **tests_requested**: []
- **tests_run**: []
- **assumptions**: ["The issue commenters' diagnoses are accurate (akshatvishu's root cause analysis and FayeSpica's workaround confirmation); code evidence at line 1562-1563 fully corroborates them.", "The reference to Tencent's upstream guard at line 613 of tokenization_hunyuan_image_3.py is correct (not verified locally, but cited by issue commenter with a plausible URL).", 'PR #2713 is the change that removed `modes`-based filtering of the two-stage topology (not verified by reading that PR, but cited by issue commenter and consistent with the config file contents).']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: Close this issue as resolved (workaround confirmed). Track the fast-fail guard improvement in a follow-up issue per @Gaohan123's request at https://github.com/vllm-project/vllm-omni/issues/4827#issuecomment-... .
- **answer_draft**: ## Root Cause

The `tencent/HunyuanImage-3.0` (Base) tokenizer does **not** contain the extended ratio tokens `<img_ratio_33>` through `<img_ratio_36>`. These tokens only exist in the `HunyuanImage-3.0-Instruct` tokenizer. When you use `--deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml` (the two-stage Instruct pipeline: AR → DiT), the AR stage init crashes at:

**`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1562-1563`**
```python
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")  # → None for Base
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]         # TypeError: None + int
```

The Base model's tokenizer has ratio tokens `<img_ratio_0>` through `<img_ratio_32>` (33 buckets). The Instruct tokenizer adds 4 more (`<img_ratio_33>` … `<img_ratio_36>`) for the extra resolution buckets used in the text+image-to-image (IT2I) pipeline.

This regression was introduced (or exposed) by PR [#2713](https://github.com/vllm-project/vllm-omni/pull/2713), which changed the config to force the two-stage Instruct topology instead of letting `modes` filter it out.

## Workaround (confirmed)

Use the **single-stage DiT config** for the Base model:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This was confirmed working by @FayeSpica in the thread.

## Config guide

| Model | Deploy config | Pipeline |
|---|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` | Single-stage DiT only |
| `tencent/HunyuanImage-3.0-Instruct` | `hunyuan_image_3_moe.yaml` | Two-stage AR → DiT |

## Improvement needed

The code should **fail fast with a clear message** when someone accidentally uses the wrong config, rather than crashing with an opaque `TypeError: NoneType + int`. The fix would mirror Tencent's own guard in their reference code ([tokenization_hunyuan_image_3.py:L613](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/bl
