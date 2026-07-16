# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

The crash is a **deploy-config mismatch**, not a model bug.

You ran the **Base** checkpoint (`tencent/HunyuanImage-3.0`) with `--deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml`, which is the **two-stage Instruct topology** (AR stage → DiT stage). During AR-stage model initialization, the code unconditionally looks up extended ratio tokens that only exist in the Instruct tokenizer:

**File:** `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1562-1563`
```python
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # ratio_36 is None → None + 1 → TypeError
```

The Base checkpoint's tokenizer vocabulary stops at `<img_ratio_32>` — it has never heard of `<img_ratio_33>` through `<img_ratio_36>`, so `convert_tokens_to_ids` returns `None`. Tencent's own reference code guards this path with a `model_version == "HunyuanImage-3.0"` check (see [tokenization_hunyuan_image_3.py#L613](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613)).

## Workaround (verified working)

Use the **single-stage DiT-only** deploy config for the Base model:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This was confirmed by contributor @FayeSpica — the Base model serves correctly with `hunyuan_image3_dit.yaml`.

## Summary table

| Checkpoint | Deploy Config |
|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` |
| `tencent/HunyuanImage-3.0-Instruct` (Instruct) | `hunyuan_image_3_moe.yaml` |

## What needs fixing

1. **Add a fast-fail guard** in `HunyuanImage3ForConditionalGeneration.__init__` (around line 1561): check whether `ratio_33` or `ratio_36` is `None` and raise a clear `ValueError` telling the user to switch to `hunyuan_image3_dit.yaml` when using the Base checkpoint.
2. **Document** the Base-vs-Instruct deploy config mapping in the README/docs.

This was first diagnosed by @akshatvishu in the comments above — the config divergence was introduced in [#2713](https://github.com/vllm-project/vllm-omni/pull/2713), which changed the MoE config to always force the two-stage topology instead of letting `modes` filter it out.

## draft_answer

## Root Cause

The crash is a **deploy-config mismatch**, not a model bug.

You ran the **Base** checkpoint (`tencent/HunyuanImage-3.0`) with `--deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml`, which is the **two-stage Instruct topology** (AR stage → DiT stage). During AR-stage model initialization, the code unconditionally looks up extended ratio tokens that only exist in the Instruct tokenizer:

**File:** `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1562-1563`
```python
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # ratio_36 is None → None + 1 → TypeError
```

The Base checkpoint's tokenizer vocabulary stops at `<img_ratio_32>` — it has never heard of `<img_ratio_33>` through `<img_ratio_36>`, so `convert_tokens_to_ids` returns `None`. Tencent's own reference code guards this path with a `model_version == "HunyuanImage-3.0"` check (see [tokenization_hunyuan_image_3.py#L613](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613)).

## Workaround (verified working)

Use the **single-stage DiT-only** deploy config for the Base model:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This was confirmed by contributor @FayeSpica — the Base model serves correctly with `hunyuan_image3_dit.yaml`.

## Summary table

| Checkpoint | Deploy Config |
|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` |
| `tencent/HunyuanImage-3.0-Instruct` (Instruct) | `hunyuan_image_3_moe.yaml` |

## What needs fixing

1. **Add a fast-fail guard** in `HunyuanImage3ForConditionalGeneration.__init__` (around line 1561): check whether `ratio_33` or `ratio_36` is `None` and raise a clear `ValueError` telling the user to switch to `hunyuan_image3_dit.yaml` when using the Base checkpoint.
2. **Document** the Base-vs-Instruct deploy config mapping in the README/docs.

This was first diagnosed by @akshatvishu in the comments above — the config divergence was introduced in [#2713](https://github.com/vllm-project/vllm-omni/pull/2713), which changed the MoE config to always force the two-stage topology instead of letting `modes` filter it out.

---

## Step diagnostics

### fetch

### draft
- **status**: success
- **summary**: Issue #4827 is a clear misconfiguration bug: the user ran the Base checkpoint (`tencent/HunyuanImage-3.0`) with the two-stage Instruct deploy config (`hunyuan_image_3_moe.yaml`), which triggers AR-stage init code that unconditionally looks up `<img_ratio_36>` in the tokenizer. The Base tokenizer only has ratio tokens up to `<img_ratio_32>`, so `convert_tokens_to_ids` returns `None`, and `None + 1` crashes with `TypeError`. The fix is to use `hunyuan_image3_dit.yaml` for the Base model (confirmed working by a contributor), and a code guard is needed to fail fast with a clear error when the Instruct config is used with the Base checkpoint.
- **findings**: ["Root cause at vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1562-1563 — `ratio_36 = tokenizer.convert_tokens_to_ids('<img_ratio_36>')` returns None for the Base tokenizer; then `self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]` crashes with `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`.", "The Base checkpoint tokenizer lacks `<img_ratio_33>` through `<img_ratio_36>` tokens that only exist in the Instruct tokenizer. Tencent's reference code guards this with a `model_version == 'HunyuanImage-3.0'` check (tokenization_hunyuan_image_3.py line 613).", 'The `hunyuan_image_3_moe.yaml` deploy config is the two-stage Instruct topology (AR → Diffusion), which is incompatible with the Base model. The Base model should use `hunyuan_image3_dit.yaml` (single-stage DiT-only).', 'Contributor @FayeSpica confirmed the Base model serves successfully with `vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code`.', 'Contributor @akshatvishu correctly diagnosed this as a deploy-config mismatch caused by PR #2713 which changed the config to force the two-stage topology instead of filtering via `modes`.']
- **files_read**: ['/rebase/vllm-omni/vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py', '/rebase/vllm-omni/vllm_omni/deploy/hunyuan_image_3_moe.yaml', '/rebase/vllm-omni/vllm_omni/deploy/hunyuan_image3_dit.yaml']
- **files_modified**: []
- **tests_requested**: []
- **tests_run**: []
- **assumptions**: ['Assuming the issue reporter is using the Base (non-Instruct) checkpoint as indicated by the model name `tencent/HunyuanImage-3.0` (not `tencent/HunyuanImage-3.0-Instruct`).', 'Assuming the deploy config `hunyuan_image_3_moe.yaml` at HEAD matches what the user ran, based on reading the file from the repo.']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: The issue is well-diagnosed in comments. Two action items remain: (1) Add a fast-fail guard in HunyuanImage3ForConditionalGeneration.__init__ around lines 1561-1563 that checks for None before computing _ratio_other_slices and raises a clear ValueError telling the user to use hunyuan_image3_dit.yaml for Base; (2) Update documentation to clarify which deploy config to use for Base vs Instruct. A tracking issue is already being requested by @Gaohan123.
- **answer_draft**: ## Root Cause

The crash is a **deploy-config mismatch**, not a model bug.

You ran the **Base** checkpoint (`tencent/HunyuanImage-3.0`) with `--deploy-config vllm_omni/deploy/hunyuan_image_3_moe.yaml`, which is the **two-stage Instruct topology** (AR stage → DiT stage). During AR-stage model initialization, the code unconditionally looks up extended ratio tokens that only exist in the Instruct tokenizer:

**File:** `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1562-1563`
```python
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # ratio_36 is None → None + 1 → TypeError
```

The Base checkpoint's tokenizer vocabulary stops at `<img_ratio_32>` — it has never heard of `<img_ratio_33>` through `<img_ratio_36>`, so `convert_tokens_to_ids` returns `None`. Tencent's own reference code guards this path with a `model_version == "HunyuanImage-3.0"` check (see [tokenization_hunyuan_image_3.py#L613](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613)).

## Workaround (verified working)

Use the **single-stage DiT-only** deploy config for the Base model:

```bash
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This was confirmed by contributor @FayeSpica — the Base model serves correctly with `hunyuan_image3_dit.yaml`.

## Summary table

| Checkpoint | Deploy Config |
|---|---|
| `tencent/HunyuanImage-3.0` (Base) | `hunyuan_image3_dit.yaml` |
| `tencent/HunyuanImage-3.0-Instruct` (Instruct) | `hunyuan_image_3_moe.yaml` |

## What needs fixing

1. **Add a fast-fail guard** in `HunyuanImage3ForConditionalGeneration.__init__` (around line 1561): check whether `ratio_33` or `ratio_36` is `None` and raise a clear `ValueError` telling the user to switch to `hunyuan_image3_dit.yaml` when using the Base checkpoint.
2. **Document** the Base-v
