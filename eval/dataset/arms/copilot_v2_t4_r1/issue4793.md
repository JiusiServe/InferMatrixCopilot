# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

This is a known bug in the `async_chunk=false` full-payload output path. The fix is PR #4792, which has been included in the v0.24 rebase (commit [`a560ed184d`](https://github.com/vllm-project/vllm-omni/commit/a560ed184d9197855f1cccf46cb1cac87b0a7138)).

**File & line (current code — post-fix):**

`vllm_omni/worker/gpu_generation_model_runner.py:463-468`
```python
if self._async_chunk:
    inter_stage_outputs, multimodal_outputs = partition_payload_list(per_req_payloads)
else:
    # See gpu_ar_model_runner: non-async-chunk ships the full payload to the next
    # stage; #4527's (None, per_req_payloads) starved the downstream stage. (PR #4792)
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

The same fix exists in `vllm_omni/worker/gpu_ar_model_runner.py:1808-1813` for the AR runner path.

## Mechanism

When `async_chunk=False`, the pipeline uses **full-payload transport**: the upstream stage must ship its complete output to the next stage via the inter-stage connector. Before the fix, the code called `partition_payload_list(per_req_payloads)` which splits payloads into inter-stage keys vs client-facing multimodal keys — and for non-empty payloads this returns `(None, ...)` for `inter_stage_outputs` because all the keys land in the client-multimodal bucket. The downstream stage (stage-1 / code2wav) then waits on the connector for input that never arrives, timing out after 300s.

With the fix, both `inter_stage_outputs` and `multimodal_outputs` receive the full `per_req_payloads`. The connector transport uses `inter_stage_outputs` to forward data to the next stage, and `multimodal_outputs` for client-facing output.

## Workaround

Your deploy config's default is `async_chunk: true` (`vllm_omni/deploy/qwen3_tts.yaml` line 14), which is unaffected by this bug. You can either:

1. **Use `async_chunk: true`** (immediate, no code change needed):
   ```yaml
   async_chunk: true
   ```

2. **Upgrade to v0.24.0rc1+** where the fix is included, then `async_chunk: false` will work correctly.

## Verification

With `async_chunk: true`:
```bash
curl -s http://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"<served-model>","input":"Hello world","voice":"Vivian","response_format":"wav"}'
```
This should return audio immediately (no hang).

## Linked Issues/PRs

- **PR #4792** — the fix (closed, cherry-picked into the v0.24 rebase at commit a560ed184d)
- **#4527** — the earlier issue that introduced the regression (`(None, per_req_payloads)` path)

## Status

The fix is in the current main branch. Since you're on vLLM-Omni 0.20.2 (commit 0899a1a), the bug is expected. Closing as **fixed in v0.24+**; please re-open if the hang persists after upgrading.
