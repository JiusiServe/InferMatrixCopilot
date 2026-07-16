# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': True, 'post': False, 'params': {}}

## fetch
- **state_updates**: {'issue_text': '{"body":"### Your current environment\\n\\n## Environment\\n\\n<details><summary><code>python collect_env.py</code></summary>\\n\\n```\\nCollecting environment information...\\nINFO 06-30 14:24:32 [patch.py:252] NVFP4 W4A4 weight_scale NaN-clamp: installed.\\n==============================\\n        System Info\\n==============================\\nOS                           : Ubuntu 22.04.5 LTS (x86_64)\\nGCC version                  : (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0\\nClang version                : Could not collect\\nCMake version                : version 4.3.4\\nLibc version                 : glibc-2.35\\n\\n==============================\\n       PyTorch Info\\n==============================\\nPyTorch version              : 2.11.0+cu128\\nIs debug build               : False\\nCUDA used to build PyTorch   : 12.8\\nROCM used to build PyTorch   : N/A\\n\\n==============================\\n      Python Environment\\n==============================\\nPython version               : 3.12.13 | packaged by conda-forge | (main, Mar  5 2026, 16:50:00) [GCC 14.3.0] (64-bit runtime)\\nPython platform              : Linux-5.15.0-94-generic-x86_64-with-glibc2.35\\n\\n==============================\\n       CUDA / GPU Info\\n==============================\\nIs CUDA available            : True\\nCUDA runtime version         : 12.2.140\\nCUDA_MODULE_LOADING set to   : \\nGPU models and configuration : \\nGPU 0: NVIDIA GeForce RTX 4090\\nGPU 1: NVIDIA GeForce RTX 4090\\nGPU 2: NVIDIA GeForce RTX 4090\\nGPU 3: NVIDIA GeForce RTX 4090\\nGPU 4: NVIDIA GeForce RTX 4090\\nGPU 5: NVIDIA GeForce RTX 4090\\nGPU 6: NVIDIA GeForce RTX 4090\\nGPU 7: NVIDIA GeForce RTX 4090\\n\\nNvidia driver version        : 595.71.05\\ncuDNN version                : Could not collect\\nHIP runtime version          : N/A\\nMIOpen runtime version       : N/A\\nIs XNNPACK available         : True\\n\\n==============================\\n          CPU Info\\n==============================\\n

## draft
- **status**: success
- **summary**: The bug is confirmed: when `async_chunk: false`, multi-stage TTS pipelines (talker → code2wav) hang because the downstream stage never receives the inter-stage payload. Root cause was a regression in #4527 that set `inter_stage_outputs` to `None` in the non-async-chunk path, starving the downstream stage. PR #4792 restored the correct behaviour — both `inter_stage_outputs` and `multimodal_outputs` now carry the full payload when `async_chunk=False`. The fix landed in the vLLM 0.24 rebase (commit a560ed184); the reporter's version (vLLM-Omni 0.20.2, commit 0899a1a) predates it. Upgrading to a version that includes the 0.24 rebase — or cherry-picking the four runner files from PR #4792 — will resolve the hang.
- **findings**: ['The bug is real: stage-1 (code2wav) times out at 300s waiting for connector input from stage-0 (talker).', "Root cause: in the `async_chunk=False` branch, `inter_stage_outputs` was set to `None` (or omitted) and only `multimodal_outputs` carried data — the downstream stage's full-payload accumulation path depends on `inter_stage_outputs`, so it starved.", 'PR #4792 fixed this by restoring `inter_stage_outputs, multimodal_outputs = payload, payload` for the non-async-chunk case in all four affected runners (GPU AR, GPU Generation, NPU AR, NPU Generation).', 'The fix is present in the current codebase (post 0.24 rebase, commit a560ed184) but the reporter is on vLLM-Omni 0.20.2 (commit 0899a1a) which predates it.', 'The `qwen3_tts.yaml` default deploy config uses `async_chunk: true` which is not affected; the bug only manifests when a user overrides to `async_chunk: false`.']
- **files_read**: ['/rebase/vllm-omni/vllm_omni/worker/gpu_generation_model_runner.py', '/rebase/vllm-omni/vllm_omni/worker/gpu_ar_model_runner.py', '/rebase/vllm-omni/vllm_omni/platforms/npu/worker/npu_generation_model_runner.py', '/rebase/vllm-omni/vllm_omni/platforms/npu/worker/npu_ar_model_runner.py', '/rebase/vllm-omni/vllm_omni/worker/omni_connector_model_runner_mixin.py', '/rebase/vllm-omni/tests/worker/test_gpu_ar_model_runner.py', '/rebase/vllm-omni/vllm_omni/platforms/xpu/worker/xpu_generation_model_runner.py']
- **files_modified**: []
- **tests_requested**: ["pytest tests/worker/test_gpu_ar_model_runner.py -v -k 'non_async'", 'pytest tests/worker/test_gpu_ar_model_runner.py::test_sample_tokens_tail_only_prefix_cache_uses_staged_cpu_hidden_states -v']
- **tests_run**: []
- **assumptions**: ["The reporter's Qwen3-TTS deploy config sets `async_chunk: false` explicitly (the default qwen3_tts.yaml uses `true`).", "The reporter's stage-0 and stage-1 are GPU runners, not NPU/XPU."]
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: The reporter should upgrade to a version that includes the vLLM 0.24 rebase (commit a560ed184 or later). Alternatively, cherry-pick the four runner files touched by PR #4792 onto their current checkout.
- **answer_draft**: ## Confirmed: `async_chunk: false` hang is a known bug — fixed in the 0.24 rebase

### What happened

When you set `async_chunk: false` on a multi-stage TTS pipeline (e.g. Qwen3-TTS talker → code2wav), the talker stage finishes successfully but **never sends the full payload** to the downstream code2wav stage. Stage-1 then waits for connector input indefinitely, hitting the 300 s timeout:

```
[Coordinator stage-1] Request speech-… timed out waiting for chunk/input (waited > 300s)
```

### Root cause

This was a regression introduced by PR #4527. In the model runner's `sample_tokens()` path, the non-`async_chunk` branch was incorrectly splitting the output so that `inter_stage_outputs` (the channel the downstream stage reads from) was set to `None`, while only `multimodal_outputs` (the client-facing channel) carried data:

```python
# Broken (pre-fix):
inter_stage_outputs, multimodal_outputs = None, per_req_payloads   # downstream starved

# Correct (post PR #4792):
inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads  # both get the full payload
```

### Fix

**PR #4792** (`[bugfix] fix audio empty bug for non-async-chunk mode`) restored the correct behaviour. The fix touches four files:

| File | Runner |
|------|--------|
| `vllm_omni/worker/gpu_ar_model_runner.py` | GPU talker (AR) runner |
| `vllm_omni/worker/gpu_generation_model_runner.py` | GPU code2wav (generation) runner |
| `vllm_omni/platforms/npu/worker/npu_ar_model_runner.py` | NPU talker runner |
| `vllm_omni/platforms/npu/worker/npu_generation_model_runner.py` | NPU code2wav runner |

These changes were incorporated into the **vLLM 0.24 rebase** (commit [`a560ed184`](https://github.com/vllm-project/vllm-omni/commit/a560ed184d9197855f1cccf46cb1cac87b0a7138)).

### Why you're seeing this

Your environment is on **vLLM-Omni 0.20.2** (commit `0899a1a`) / **vLLM 0.23.0**, which predates the fix.

### What to do

1. **Upgrade** to a vLLM-Omni build that includes the 0.24 rebase (comm
- **draft_answer**: ## Confirmed: `async_chunk: false` hang is a known bug — fixed in the 0.24 rebase

### What happened

When you set `async_chunk: false` on a multi-stage TTS pipeline (e.g. Qwen3-TTS talker → code2wav), the talker stage finishes successfully but **never sends the full payload** to the downstream code2wav stage. Stage-1 then waits for connector input indefinitely, hitting the 300 s timeout:

```
[Coordinator stage-1] Request speech-… timed out waiting for chunk/input (waited > 300s)
```

### Root cause

This was a regression introduced by PR #4527. In the model runner's `sample_tokens()` path, the non-`async_chunk` branch was incorrectly splitting the output so that `inter_stage_outputs` (the channel the downstream stage reads from) was set to `None`, while only `multimodal_outputs` (the client-facing channel) carried data:

```python
# Broken (pre-fix):
inter_stage_outputs, multimodal_outputs = None, per_req_payloads   # downstream starved

# Correct (post PR #4792):
inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads  # both get the full payload
```

### Fix

**PR #4792** (`[bugfix] fix audio empty bug for non-async-chunk mode`) restored the correct behaviour. The fix touches four files:

| File | Runner |
|------|--------|
| `vllm_omni/worker/gpu_ar_model_runner.py` | GPU talker (AR) runner |
| `vllm_omni/worker/gpu_generation_model_runner.py` | GPU code2wav (generation) runner |
| `vllm_omni/platforms/npu/worker/npu_ar_model_runner.py` | NPU talker runner |
| `vllm_omni/platforms/npu/worker/npu_generation_model_runner.py` | NPU code2wav runner |

These changes were incorporated into the **vLLM 0.24 rebase** (commit [`a560ed184`](https://github.com/vllm-project/vllm-omni/commit/a560ed184d9197855f1cccf46cb1cac87b0a7138)).

### Why you're seeing this

Your environment is on **vLLM-Omni 0.20.2** (commit `0899a1a`) / **vLLM 0.23.0**, which predates the fix.

### What to do

1. **Upgrade** to a vLLM-Omni build that includes the 0.24 rebase (comm
- **state_updates**: {'draft_answer': "## Confirmed: `async_chunk: false` hang is a known bug — fixed in the 0.24 rebase\n\n### What happened\n\nWhen you set `async_chunk: false` on a multi-stage TTS pipeline (e.g. Qwen3-TTS talker → code2wav), the talker stage finishes successfully but **never sends the full payload** to the downstream code2wav stage. Stage-1 then waits for connector input indefinitely, hitting the 300 s timeout:\n\n```\n[Coordinator stage-1] Request speech-… timed out waiting for chunk/input (waited > 300s)\n```\n\n### Root cause\n\nThis was a regression introduced by PR #4527. In the model runner's `sample_tokens()` path, the non-`async_chunk` branch was incorrectly splitting the output so that `inter_stage_outputs` (the channel the downstream stage reads from) was set to `None`, while only `multimodal_outputs` (the client-facing channel) carried data:\n\n```python\n# Broken (pre-fix):\ninter_stage_outputs, multimodal_outputs = None, per_req_payloads   # downstream starved\n\n# Correct (post PR #4792):\ninter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads  # both get the full payload\n```\n\n### Fix\n\n**PR #4792** (`[bugfix] fix audio empty bug for non-async-chunk mode`) restored the correct behaviour. The fix touches four files:\n\n| File | Runner |\n|------|--------|\n| `vllm_omni/worker/gpu_ar_model_runner.py` | GPU talker (AR) runner |\n| `vllm_omni/worker/gpu_generation_model_runner.py` | GPU code2wav (generation) runner |\n| `vllm_omni/platforms/npu/worker/npu_ar_model_runner.py` | NPU talker runner |\n| `vllm_omni/platforms/npu/worker/npu_generation_model_runner.py` | NPU code2wav runner |\n\nThese changes were incorporated into the **vLLM 0.24 rebase** (commit [`a560ed184`](https://github.com/vllm-project/vllm-omni/commit/a560ed184d9197855f1cccf46cb1cac87b0a7138)).\n\n### Why you're seeing this\n\nYour environment is on **vLLM-Omni 0.20.2** (commit `0899a1a`) / **vLLM 0.23.0**, which predates the fix.\n\n### What to do\n\n1. **Upgrade
