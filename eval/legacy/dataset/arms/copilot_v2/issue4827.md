# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4827, 'report_only': True, 'post': False, 'params': {}}

## fetch
- **state_updates**: {'issue_text': '{"body":"### Your current environment\\n\\n<details>\\n<summary>The output of <code>python collect_env.py</code></summary>\\n\\n```text\\n==============================\\n        System Info\\n==============================\\nOS                           : Ubuntu 22.04.5 LTS (aarch64)\\nGCC version                  : (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0\\nClang version                : 15.0.7\\nCMake version                : version 4.3.2\\nLibc version                 : glibc-2.35\\n\\n==============================\\n       PyTorch Info\\n==============================\\nPyTorch version              : 2.10.0+cpu\\nIs debug build               : False\\nCUDA used to build PyTorch   : None\\nROCM used to build PyTorch   : N/A\\n\\n==============================\\n      Python Environment\\n==============================\\nPython version               : 3.12.13 (main, May 19 2026, 08:33:02) [GCC 11.4.0] (64-bit runtime)\\nPython platform              : Linux-5.10.0-182.0.0.95.r1941_123.hce2.aarch64-aarch64-with-glibc2.35\\n\\n==============================\\n       CUDA / GPU Info\\n==============================\\nIs CUDA available            : False\\nCUDA runtime version         : No CUDA\\nCUDA_MODULE_LOADING set to   : N/A\\nGPU models and configuration : No CUDA\\nNvidia driver version        : No CUDA\\ncuDNN version                : No CUDA\\nHIP runtime version          : N/A\\nMIOpen runtime version       : N/A\\nIs XNNPACK available         : True\\n\\n==============================\\n          CPU Info\\n==============================\\nArchitecture:                         aarch64\\nCPU op-mode(s):                       64-bit\\nByte Order:                           Little Endian\\nCPU(s):                               320\\nOn-line CPU(s) list:                  0-319\\nVendor ID:                            HiSilicon\\nBIOS Vendor ID:                       HiSilicon\\nBIOS Model name:                      Kunpeng 920 7285Z\\nModel:    

## draft
- **status**: success
- **summary**: The crash occurs because `tencent/HunyuanImage-3.0` (Base checkpoint) is being loaded with the Instruct deploy config `hunyuan_image_3_moe.yaml`, which forces the two-stage AR+DiT topology. The Base tokenizer lacks extended ratio tokens `<img_ratio_33>` through `<img_ratio_36>`, causing `tokenizer.convert_tokens_to_ids("<img_ratio_36>")` to return `None`, and the unguarded `None + 1` at init time raises `TypeError`. The fix is to use the correct single-stage DiT deploy config: `hunyuan_image3_dit.yaml`. Additionally, a code guard should be added to fail fast with a clear error when loading the Base model with the MoE/Instruct config.
- **findings**: ['Root cause: `HunyuanImage3ForConditionalGeneration.__init__` at line 1561-1563 calls `tokenizer.convert_tokens_to_ids("<img_ratio_36>")` which returns `None` for the Base tokenizer, and `None + 1` crashes with TypeError.', 'The `hunyuan_image_3_moe.yaml` deploy config forces a two-stage (AR → DiT) Instruct topology; the Base checkpoint is a single-stage DiT model and must use `hunyuan_image3_dit.yaml`.', '@akshatvishu identified that the MoE config forces the two-stage topology (ref: PR #2713), overriding the older config that let `modes` filter it out.', '@FayeSpica confirmed that `vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml --trust-remote-code` works correctly.', 'No guard exists in the current code at lines 1559-1564: `ratio_33` and `ratio_36` can be `None` when the Base tokenizer is loaded, and the code should handle this gracefully with a descriptive error.', '@Gaohan123 requested a separate tracking issue for the guard/diagnostic improvement.']
- **files_read**: ['/rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2/runs/issue4827/run-20260711-232303/evidence/issue_text.txt', '/rebase/vllm-omni/vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py', '/rebase/vllm-omni/vllm_omni/deploy/hunyuan_image_3_moe.yaml', '/rebase/vllm-omni/vllm_omni/deploy/hunyuan_image3_dit.yaml']
- **files_modified**: []
- **tests_requested**: []
- **tests_run**: []
- **assumptions**: ['The crash is reproducible exactly as described in the issue when using the Base checkpoint with the MoE deploy config.', 'The Base model uses `hunyuan_image3_dit` pipeline while Instruct uses `hunyuan_image_3_moe` pipeline.', 'The `_ratio_other_slices` list being empty (rather than containing a None-based slice) would be a safe fallback for comprehension mode, but a guard is needed regardless.']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: Open a new issue (as requested by @Gaohan123) to track adding a guard in `HunyuanImage3ForConditionalGeneration.__init__` that fails fast with a clear error message if `<img_ratio_36>` (or `<img_ratio_33>`) is not found in the tokenizer when the model is configured with a MoE pipeline. Also consider documenting the deploy-config mapping clearly.
- **answer_draft**: ## Diagnosis confirmed — wrong deploy config for Base checkpoint

Thanks for the detailed report! The crash is caused by loading the **Base** checkpoint (`tencent/HunyuanImage-3.0`) with the **Instruct** deploy config (`hunyuan_image_3_moe.yaml`).

### Root cause

`hunyuan_image_3_moe.yaml` forces a two-stage AR → DiT topology (designed for Instruct). At init time, the `HunyuanImage3ForConditionalGeneration` model looks up extended ratio tokens `<img_ratio_33>` through `<img_ratio_36>` from the tokenizer:

```python
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # 💥 None + 1
```

The Base tokenizer doesn't have these tokens (they exist only in the Instruct tokenizer), so `convert_tokens_to_ids` returns `None`, and `None + 1` raises `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`.

This is the same pattern Tencent's reference code guards against by checking `model_version == "HunyuanImage-3.0"` — see [tokenization_hunyuan_image_3.py#L613](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613).

### Immediate fix: use the correct deploy config

The Base checkpoint is a single-stage DiT model. Use `hunyuan_image3_dit.yaml`:

```shell
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This has been verified to work correctly. For the Instruct checkpoint (`tencent/HunyuanImage-3.0-Instruct`), you should use `hunyuan_image_3_moe.yaml` which wires up the full AR → DiT pipeline with KV reuse.

### Follow-up improvement

As [@akshatvishu](https://github.com/akshatvishu) suggested, the code should **fail fast with a clear error message** if someone accidentally loads the Base model with the MoE/Instruct config. Instead of the cryptic `NoneType + int` crash, it should say some
- **draft_answer**: ## Diagnosis confirmed — wrong deploy config for Base checkpoint

Thanks for the detailed report! The crash is caused by loading the **Base** checkpoint (`tencent/HunyuanImage-3.0`) with the **Instruct** deploy config (`hunyuan_image_3_moe.yaml`).

### Root cause

`hunyuan_image_3_moe.yaml` forces a two-stage AR → DiT topology (designed for Instruct). At init time, the `HunyuanImage3ForConditionalGeneration` model looks up extended ratio tokens `<img_ratio_33>` through `<img_ratio_36>` from the tokenizer:

```python
ratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")
ratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")
self._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # 💥 None + 1
```

The Base tokenizer doesn't have these tokens (they exist only in the Instruct tokenizer), so `convert_tokens_to_ids` returns `None`, and `None + 1` raises `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'`.

This is the same pattern Tencent's reference code guards against by checking `model_version == "HunyuanImage-3.0"` — see [tokenization_hunyuan_image_3.py#L613](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613).

### Immediate fix: use the correct deploy config

The Base checkpoint is a single-stage DiT model. Use `hunyuan_image3_dit.yaml`:

```shell
vllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \
  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \
  --trust-remote-code
```

This has been verified to work correctly. For the Instruct checkpoint (`tencent/HunyuanImage-3.0-Instruct`), you should use `hunyuan_image_3_moe.yaml` which wires up the full AR → DiT pipeline with KV reuse.

### Follow-up improvement

As [@akshatvishu](https://github.com/akshatvishu) suggested, the code should **fail fast with a clear error message** if someone accidentally loads the Base model with the MoE/Instruct config. Instead of the cryptic `NoneType + int` crash, it should say some
- **state_updates**: {'draft_answer': '## Diagnosis confirmed — wrong deploy config for Base checkpoint\n\nThanks for the detailed report! The crash is caused by loading the **Base** checkpoint (`tencent/HunyuanImage-3.0`) with the **Instruct** deploy config (`hunyuan_image_3_moe.yaml`).\n\n### Root cause\n\n`hunyuan_image_3_moe.yaml` forces a two-stage AR → DiT topology (designed for Instruct). At init time, the `HunyuanImage3ForConditionalGeneration` model looks up extended ratio tokens `<img_ratio_33>` through `<img_ratio_36>` from the tokenizer:\n\n```python\nratio_33 = tokenizer.convert_tokens_to_ids("<img_ratio_33>")\nratio_36 = tokenizer.convert_tokens_to_ids("<img_ratio_36>")\nself._ratio_other_slices = [(ratio_33, ratio_36 + 1)]  # 💥 None + 1\n```\n\nThe Base tokenizer doesn\'t have these tokens (they exist only in the Instruct tokenizer), so `convert_tokens_to_ids` returns `None`, and `None + 1` raises `TypeError: unsupported operand type(s) for +: \'NoneType\' and \'int\'`.\n\nThis is the same pattern Tencent\'s reference code guards against by checking `model_version == "HunyuanImage-3.0"` — see [tokenization_hunyuan_image_3.py#L613](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/hunyuan_image_3/tokenization_hunyuan_image_3.py#L613).\n\n### Immediate fix: use the correct deploy config\n\nThe Base checkpoint is a single-stage DiT model. Use `hunyuan_image3_dit.yaml`:\n\n```shell\nvllm serve tencent/HunyuanImage-3.0 --omni --port 8091 \\\n  --deploy-config vllm_omni/deploy/hunyuan_image3_dit.yaml \\\n  --trust-remote-code\n```\n\nThis has been verified to work correctly. For the Instruct checkpoint (`tencent/HunyuanImage-3.0-Instruct`), you should use `hunyuan_image_3_moe.yaml` which wires up the full AR → DiT pipeline with KV reuse.\n\n### Follow-up improvement\n\nAs [@akshatvishu](https://github.com/akshatvishu) suggested, the code should **fail fast with a clear error message** if someone accidentally loads the Base model with the MoE/Instruct config. Instead
