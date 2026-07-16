---
name: fix-talker-truncated-prefill-prefix-cache-key-cap
description: Fix talker-stage crash "size of tensor a (6) must match b (9)" caused by OmniTensorPrefixCache's 512 MiB per-key cap dropping hidden_states.layer_N — declare the keys as required, do NOT raise the cap globally or disable prefix caching
trigger: RuntimeError 'The size of tensor a (6) must match the size of tensor b (9)' in _get_talker_assistant_parts (stage-1 talker prefill), or WARNING 'Skipping mm prefix cache key hidden_states.layer_N' in stage-0 log, in omni_qwen3-omni_test
modules: [worker_runner, model_executor]
status: active
created_at: 2026-06-10
last_used_at: 2026-07-11
run_count: 54
---

## Symptom

- `tests/e2e/online_serving/test_qwen3_omni.py::test_mix_to_text_audio_001[default]` fails; stage-1
  (`StageEngineCoreProc_stage1_replica0`) dies with:
  `RuntimeError: The size of tensor a (6) must match the size of tensor b (9) at non-singleton dimension 0`
  at `vllm_omni/model_executor/models/qwen3_omni/qwen3_omni.py::_get_talker_assistant_parts`
  (`input_embeds = assistant_text_hidden + assistant_codec_hidden`).
- All remaining tests in the file then fail instantly (`EngineDeadError`) because the OmniServer
  fixture is session-scoped and stage 1 is dead. The watchdog kills pytest (rc=143).
- Decoding the shapes: `assistant_codec_hidden` is always 9 rows; `assistant_text_hidden` == 6
  (0 + 4 pad + 1 BOS + 1 zero-fill) means `thinker_embed[im_start_index:segment_end_index]` was
  **empty**, i.e. the `embed.prefill` tensor from stage 0 is much shorter than the prompt.

## Diagnose (generic recipe for cross-stage truncation)

1. Grep the stage-0 section of the test log for the cap warning:
   `grep "Skipping mm prefix cache key" <test.log>` → hits on `hidden_states.layer_0` /
   `hidden_states.layer_24` confirm this skill applies.
2. Confirm with payload telemetry — connector send sizes per request:
   `grep "_send_single_request" <test.log>`.
   Healthy: all mix-test requests ~21–22 MB. Broken: first request ~21 MB (prefix-cache miss),
   subsequent identical-prompt requests ~1.4 MB (prefix-cache hit, truncated to suffix rows).
3. Attribute before debugging: compare with the same test's log from the **last passing run**
   (`rebase_logs/runs/<prev-run>/tests/00_omni_qwen3-omni_test.log`). Check whether the vLLM
   version line (`Initializing a V1 LLM engine (vX.Y...+g<sha>)`) is identical — if so, the
   regression is in the vllm-omni tree (merged origin/main commits or module-agent commits),
   NOT in the vLLM bump. `git log -S<warning text> --all` finds the introducing commit fast.

Root cause chain (first seen with upstream vllm-omni #3689 / commit 57227dc7):
- The test force-enables prefix caching on stages 0/1 via `--stage-overrides`.
- Qwen3-omni thinker packs per-token `hidden_states.layer_0` (embeddings) and
  `hidden_states.layer_{accept_hidden_layer}` rows into the thinker→talker payload; on a
  prefix-cache hit only suffix tokens are executed, and the cached prefix rows must be
  reconstructed from `OmniTensorPrefixCache`.
- #3689 added `_MAX_MM_CACHE_BYTES_PER_KEY = 512 MiB` (tuned for qwen3-tts). With a large KV
  cache (e.g. 682,896 tokens on L20X → 2667.6 MiB per 2048-dim bf16 key) both layer keys are
  silently dropped → prefix-hit requests ship truncated `embed.prefill` → talker crash.

## Anti-patterns (DO NOT DO THIS)

- Do NOT raise/delete `_MAX_MM_CACHE_BYTES_PER_KEY` globally — it is a deliberate upstream OOM
  guard for qwen3-tts-class models.
- Do NOT disable prefix caching in the test/deploy config to make the test pass — it masks the
  correctness bug and regresses perf.
- Do NOT patch the talker side to tolerate short embeds — the payload is already wrong by then.

## Fix

Model-declared exemption, following the existing `requires_full_prefix_cached_hidden_states` /
`deferred_prefix_cache_mm_keys` pattern (4 small edits):

1. `vllm_omni/core/prefix_cache.py` — `OmniTensorPrefixCache.__init__` takes
   `required_mm_cache_keys: set[str] | None`; in `maybe_init_missing_mm_cache_keys`, keys in this
   set bypass the size cap (log a `warning_once` with the actual MiB instead of skipping).
2. `vllm_omni/worker/gpu_model_runner.py` — when constructing the cache in
   `initialize_metadata_builders`, pass
   `required_mm_cache_keys=set(getattr(getattr(self, "model", None), "required_prefix_cache_mm_keys", ()) or ())`.
3. `vllm_omni/model_executor/models/qwen3_omni/qwen3_omni.py` — thinker branch of `__init__`:

```python
self.required_prefix_cache_mm_keys = {"hidden_states.layer_0"}
accept_layer = getattr(talker_config, "accept_hidden_layer", None)
if accept_layer is not None:
    self.required_prefix_cache_mm_keys.add(f"hidden_states.layer_{int(accept_layer)}")
```

4. `tests/core/test_prefix_cache.py` — unit test: monkeypatch the cap to 1 byte, assert required
   keys still get cached and optional oversized keys are skipped.

Key naming: `flatten_payload` (vllm_omni/data_entry_keys.py) maps
`{"hidden_states": {"layers": {N: t}}}` → `"hidden_states.layer_N"`; declare the flattened names.

## Verification

- `python -m pytest tests/core/test_prefix_cache.py -q` → all pass.
- `CUDA_VISIBLE_DEVICES=0,1 python -m pytest -s -v tests/e2e/online_serving/test_qwen3_omni.py -m 'core_model' --run-level 'core_model'` → 4 passed.
- Stage-0 log now shows `... exceeds the 512.0 MiB cap ... but is required for downstream-stage
  correctness; allocating it on CPU anyway`, and `_send_single_request` sizes are ~21 MB for ALL
  mix-test requests (not just the first).

## Watch Out

- Any model whose downstream stage consumes **full-prompt per-token** mm outputs must declare
  `required_prefix_cache_mm_keys` when stage-0 prefix caching can be enabled. Qwen2.5-omni does
  not use the layer-capture mechanism today; re-check if that changes.
- The bypassed cache lives in host RAM (~2.6 GiB per key here). Fine on CI hosts with TB-scale
  RAM; flag it if the host is small.
- This root cause came from vllm-omni `origin/main`, not the vLLM bump — the fix belongs
  upstream in vllm-omni, not as a rebase-only adaptation. File/track an upstream PR.
