# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

In non-`async_chunk` mode, the upstream stage must ship its full output payload to the downstream stage through `OmniModelRunnerOutput.inter_stage_outputs`. A prior change (#4527) split the payload via `partition_payload_list()` *unconditionally*, and in the non-async-chunk branch it set `inter_stage_outputs` to `None` — keeping only the client-facing keys in `multimodal_outputs`.

The downstream stage's connector (`accumulate_full_payload_output`) reads from `inter_stage_outputs`. With that field `None`, it never receives any data and times out after 300s:

```
[Coordinator stage-1] Request speech-... timed out waiting for chunk/input (waited > 300s)
Marking 1 request(s) as FINISHED_ERROR after waiting > 300s for connector input
```

The bug affects **four** runner files — both GPU and NPU, both AR (`gpu_ar_model_runner`, `npu_ar_model_runner`) and generation (`gpu_generation_model_runner`, `npu_generation_model_runner`):

| File | Line | Defective pattern (pre-fix) |
|---|---|---|
| `vllm_omni/worker/gpu_generation_model_runner.py` | 468 | `inter_stage_outputs, multimodal_outputs = None, per_req_payloads` |
| `vllm_omni/worker/gpu_ar_model_runner.py` | 1816 | `pooler_inter, pooler_client = None, pooler_output` |
| `vllm_omni/platforms/npu/worker/npu_generation_model_runner.py` | ~484 | same as GPU gen |
| `vllm_omni/platforms/npu/worker/npu_ar_model_runner.py` | 1168 | same as GPU AR |

## Fix

PR [#4792](https://github.com/vllm-project/vllm-omni/pull/4792) changes the non-async-chunk branch to ship the full payload through **both** fields:

```python
# gpu_generation_model_runner.py:468 (post-fix)
inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads

# gpu_ar_model_runner.py:1816 (post-fix)
pooler_inter, pooler_client = pooler_output, pooler_output
```

PR #4792 was closed as "CONFLICTING" but its substantive changes were cherry-picked into the vLLM 0.24 rebase commit [`a560ed1`](https://github.com/vllm-project/vllm-omni/commit/a560ed184d9197855f1cccf46cb1cac87b0a7138). The current `main` tree already carries the fix (confirmed at the file:line locations above).

## Workaround

1. **Immediate**: Use `async_chunk: true` in your deploy config — this is the default in `vllm_omni/deploy/qwen3_tts.yaml` and does not trigger the bug.
2. **Proper fix**: Update to a vLLM-Omni tree that includes commit `a560ed1` or later (i.e., the vLLM 0.24 rebase or newer).

## Verification

After updating, run a non-async-chunk multi-stage pipeline and confirm the request completes instead of timing out. The unit test added by PR #4792 can also be run:

```bash
pytest tests/worker/test_gpu_ar_model_runner.py::test_build_omni_output_non_async_chunk_accumulates_full_payload -v
```

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
