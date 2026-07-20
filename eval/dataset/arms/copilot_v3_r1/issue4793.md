# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4793, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
PR #4527 changed the non-async-chunk branch in sample_tokens() to return `inter_stage_outputs, multimodal_outputs = None, per_req_payloads`. The downstream stage consumes data exclusively through `inter_stage_outputs` / `accumulate_full_payload_output`, so `None` starved it. Evidence: vllm_omni/worker/gpu_generation_model_runner.py (pre-fix) and vllm_omni/worker/gpu_ar_model_runner.py (pre-fix) — compared with post-fix lines 464-468 (generation) and 1809-1815 (AR) which carry the `#4527's (None, per_req_payloads) starved` comment.

### Fix
Merge or cherry-pick PR #4792 (or its included commit a560ed184). The fix changes non-async-chunk to `inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads` so the full payload reaches the downstream stage through both channels.

### Workaround
Set `async_chunk: true` in all stages of the deploy YAML (the default `vllm_omni/deploy/qwen3_tts.yaml` already uses this). The async_chunk path is unaffected by this bug.

### Preconditions
The fix requires no special hardware or version constraints beyond what the reporter already has (vLLM 0.23+, 8×RTX 4090). Simply updating to a commit that includes PR #4792 is sufficient.

### Verification
After updating, run: `curl -s http://localhost:8000/v1/audio/speech -H 'Content-Type: application/json' -d '{"model":"<served-model>","input":"Hello world","voice":"Vivian","response_format":"wav"}'` — should return audio within seconds with `async_chunk: false` set, no 300s timeout.

### Prevention
The fix ships with a regression test: `tests/worker/test_gpu_ar_model_runner.py::test_build_omni_output_non_async_chunk_accumulates_full_payload`. A guard comment at each affected site references both #4527 (the regression) and #4792 (the fix), so future changes to this path are warned about the starvation risk. Consider adding a CI gate that runs multi-stage e2e with `async_chunk: false` to catch similar regressions before merge.

### Disposition
close

### Additional context
## Root Cause

The hang is caused by a regression introduced in PR #4527. In the `sample_tokens()` methods of the GPU model runners, when `async_chunk` is disabled (`false`), the code was setting `inter_stage_outputs` to `None` while placing the actual payload into `multimodal_outputs`:

```python
# PRE-FIX (broken):
inter_stage_outputs, multimodal_outputs = None, per_req_payloads
```

The downstream connector stage consumes data through `inter_stage_outputs` (via `accumulate_full_payload_output`), not through `multimodal_outputs`. With `inter_stage_outputs = None`, the connector received no data and timed out after 300s.

This affected all four model runners:
- `vllm_omni/worker/gpu_generation_model_runner.py` (code2wav / non-AR stages)
- `vllm_omni/worker/gpu_ar_model_runner.py` (AR stages like talker)
- `vllm_omni/platforms/npu/worker/npu_generation_model_runner.py`
- `vllm_omni/platforms/npu/worker/npu_ar_model_runner.py`

## Fix (already merged — PR #4792)

PR #4792 changed the non-async-chunk branch to ship the full payload through **both** channels:

```python
# FIX (PR #4792):
# See gpu_ar_model_runner: non-async-chunk ships the full payload to the next
# stage; #4527's (None, per_req_payloads) starved the downstream stage. (PR #4792)
inter_stage_outputs, multimodal_outputs = per_req_payloads, per_req_payloads
```

The fix was merged and is included in the vLLM 0.24 rebase commit `a560ed184d9197855f1cccf46cb1cac87b0a7138` (as noted by @akshatvishu).

## What you should do

Your current commit `0899a1a` (vLLM-Omni 0.20.2) predates this fix. Update to a version that includes PR #4792:

```bash
# Option 1: Update to main (includes the fix)
git checkout main && git pull

# Option 2: Stay on your branch but cherry-pick the fix
git cherry-pick a560ed184
```

## Workaround (if you cannot update immediately)

Set `async_chunk: true` in your deploy YAML — the default `vllm_omni/deploy/qwen3_tts.yaml` already does this and is confirmed working:

```yaml
stages:
  - name: stage-0
    async_chunk: true  # works
  - name: stage-1
    async_chunk: true  # works
```

## Verification

After updating, run your same curl command — the request should complete within seconds with valid audio output instead of timing out:

```bash
curl -s http://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"<served-model>","input":"Hello world","voice":"Vivian","response_format":"wav"}'
```

Related: the fix ships with a dedicated unit test — `tests/worker/test_gpu_ar_model_runner.py::test_build_omni_output_non_async_chunk_accumulates_full_payload` — which verifies that non-async-chunk accumulates the full payload for downstream stages.
