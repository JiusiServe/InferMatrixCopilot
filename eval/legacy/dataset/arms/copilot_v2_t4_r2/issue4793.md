# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

The hang is caused by a starvation bug in the non-async-chunk inter-stage data path.  In `sample_tokens()`, the call to `partition_payload_list()` returns `(None, per_req_payloads)` for the inter-stage half when the async-chunk split logic decides there is no chunk to forward.  In **non-async-chunk** mode the full payload must be shipped to the next stage, not dropped — the downstream stage (code2wav) therefore never receives input and the coordinator times out after 300 s.

**Affected files (before fix):**

* `vllm_omni/worker/gpu_generation_model_runner.py` — `sample_tokens()` (code2wav stage)
* `vllm_omni/worker/gpu_ar_model_runner.py` — `sample_tokens()` (talker stage)

## Fix

PR [#4792](https://github.com/vllm-project/vllm-omni/pull/4792) changed the non-async-chunk branch to assign the full payload to **both** `inter_stage_outputs` and `multimodal_outputs`:

```python
# gpu_generation_model_runner.py (sample_tokens, ~line 463)
if self._async_chunk:
    inter_stage_outputs, multimodal_outputs = partition_payload_list(per_req_payloads)
else:
    # non-async-chunk ships the full payload to the next stage
    inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

The same pattern is applied in `gpu_ar_model_runner.py` at line 1808-1816.

PR #4792 was closed and its changes were cherry-picked into the vLLM **0.24** rebase commit `a560ed184d9197855f1cccf46cb1cac87b0a7138`.  The code comment referencing `#4527` and `PR #4792` confirms this.

## Checking your version

Your environment reports **vLLM-Omni 0.20.2** at commit `0899a1a`.  This likely **predates** the v0.24 rebase that includes the fix.  You can verify by checking whether the fix pattern above exists in your local `vllm_omni/worker/gpu_generation_model_runner.py`.

## Workaround (immediate)

Use `async_chunk: true` — this is the default in `vllm_omni/deploy/qwen3_tts.yaml` and works correctly, as you confirmed.

## Resolution

Rebase to a commit that includes the v0.24 upstream merge (e.g. `a560ed184` or later) which carries PR #4792.  If you are already on a commit that contains the fix and still see the hang, please re-open with a fresh server log — there may be a secondary issue in the full-payload connector / coordinator wake-up path that needs deeper investigation.
