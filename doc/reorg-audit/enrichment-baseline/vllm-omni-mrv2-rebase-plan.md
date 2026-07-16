# Rebase Plan: Align vLLM-Omni MR V2 with Upstream vLLM

> **Target:** Rebase `vllm_omni/worker_v2/` (from PR #2509) against vLLM HEAD (`78743ab5b`, v0.23.0rc2)  
> **Author:** (auto-generated)  
> **Date:** 2026-06-12  
> **Status:** Plan  

---

## 1. Situation Assessment

### 1.1 Current State

| Component | Version / Branch | Notes |
|-----------|-----------------|-------|
| **vLLM upstream** | `78743ab5b` (v0.23.0rc2) | MR V2 in `vllm/v1/worker/gpu/` |
| **vLLM-Omni MR V2 PR** | PR #2509 (`dev/migrate-MR-v2`) | ~8,083 lines, created 2026-04-05 |
| **vLLM-Omni working branch** | `dev/vllm-align` | Rebasing onto v0.23.0 baseline |

### 1.2 Problem

PR #2509 was designed against vLLM as of ~April 2026. Since then, vLLM's MR V2 has received **31 commits on `model_runner.py` alone** plus numerous API changes in `model_states/`, `cudagraph_utils.py`, `pp_utils.py`, `dp_utils.py`, `sample/`, `kv_connector.py`, and `outputs.py`. At least **6 breaking API changes** directly affect the code in `vllm_omni/worker_v2/`.

### 1.3 Dependency Surface

vLLM-Omni's `worker_v2/` imports from these upstream modules:

| Upstream Module | What vLLM-Omni Uses |
|---|---|
| `vllm.v1.worker.gpu.model_runner` | `GPUModelRunner`, `BatchDescriptor`, `BatchExecutionDescriptor`, `ExecuteModelState`, `IntermediateTensors`, `build_slot_mappings_by_layer`, `get_uniform_token_count` |
| `vllm.v1.worker.gpu.model_states` | `init_model_state`, `ModelState` |
| `vllm.v1.worker.gpu.model_states.default` | `DefaultModelState` (base class for `OmniModelState`) |
| `vllm.v1.worker.gpu.input_batch` | `InputBatch` |
| `vllm.v1.worker.gpu.states` | `RequestState` |
| `vllm.v1.worker.gpu.mm.encoder_cache` | `EncoderCache` |
| `vllm.v1.worker.gpu.dp_utils` | `sync_cudagraph_and_dp_padding` (**renamed**) |
| `vllm.v1.worker.gpu.pp_utils` | `pp_receive`, `pp_broadcast` (**replaced by PPHandler**) |
| `vllm.v1.core.sched.output` | `SchedulerOutput`, `NewRequestData`, `GrammarOutput` |
| `vllm.v1.outputs` | `AsyncModelRunnerOutput`, `ModelRunnerOutput` |
| `vllm.config` / `vllm.config.compilation` | `VllmConfig`, `CUDAGraphMode` |
| `vllm.forward_context` | `set_forward_context` |
| `vllm.logger` | `init_logger` |

---

## 2. Breaking API Changes in Upstream (Since April 2026)

### 2.1 `pp_receive` / `pp_broadcast` → `PPHandler` class

**Severity: HIGH** | **Files affected:** `omni_ar_model_runner.py`, `omni_generation_model_runner.py`

The old pattern:
```python
# Old API (what PR #2509 code expects)
from vllm.v1.worker.gpu.pp_utils import pp_receive, pp_broadcast

# Non-last rank: receive sampled tokens
sampled_token_ids, num_sampled, num_rejected, idx_mapping_np = pp_receive(...)

# Last rank: broadcast sampled tokens
pp_broadcast(sampled_token_ids, num_sampled, num_rejected, ...)
```

New API:
```python
# New API (current vLLM HEAD)
from vllm.v1.worker.gpu.pp_utils import PPHandler

# In __init__: self.pp_handler = PPHandler(max_num_reqs, num_speculative_steps, device)

# Non-last rank: receive (async, consumed pp_size steps later)
all_decode_next = self.pp_handler.receive(input_batch)
# ...optimistic postprocess...
prev_outputs = self.pp_handler.get_prev_sampled_outputs()  # consumed later

# Last rank: broadcast
self.pp_handler.broadcast(sampled_token_ids, num_sampled, num_rejected, input_batch)
```

**Required action:** Rewrite PP rank handling in `OmniARModelRunner.sample_tokens()` and `OmniGenerationModelRunner` to use `PPHandler`.

### 2.2 `sync_cudagraph_and_dp_padding` → `dispatch_cg_and_sync_dp`

**Severity: HIGH** | **File affected:** `omni_model_runner.py`

Old signature:
```python
batch_desc, num_tokens_across_dp = sync_cudagraph_and_dp_padding(
    self.cudagraph_manager, desired_batch_desc, num_toks, num_reqs,
    uniform_tok_count, self.dp_size, self.dp_rank
)
```

New signature (dispatch logic internalized):
```python
batch_desc, num_tokens_across_dp = dispatch_cg_and_sync_dp(
    self.cudagraph_manager,
    num_reqs, num_toks, uniform_tok_count,
    self.dp_size, self.dp_rank,
    need_eager=is_profile or skip_compiled,
)
```

**Required action:** Update `OmniGPUModelRunner._dispatch_batch_descriptor()` to match new signature. The internal `BatchExecutionDescriptor` construction is now done inside `dispatch_cg_and_sync_dp`, so the method should be simplified or removed.

### 2.3 `postprocess` → `postprocess_sampled`

**Severity: MEDIUM** | **File affected:** `omni_ar_model_runner.py`

```python
# Old
self.postprocess(idx_mapping, sampled_token_ids, num_sampled, num_rejected, query_start_loc)

# New
self.postprocess_sampled(idx_mapping, sampled_token_ids, num_sampled, num_rejected, query_start_loc)
```

**Required action:** Update calls.

### 2.4 `KVConnector.post_forward` signature change

**Severity: MEDIUM** | **Files affected:** `omni_model_runner.py`, `omni_ar_model_runner.py`

```python
# Old (passes full scheduler_output)
kv_connector_output = self.kv_connector.post_forward(scheduler_output)

# New (passes just finished_req_ids)
kv_connector_output = self.kv_connector.post_forward(finished_req_ids)
```

**Required action:** Extract `finished_req_ids = scheduler_output.finished_req_ids` and pass that instead.

### 2.5 `ExecuteModelState` field changes

**Severity: MEDIUM** | **File affected:** `omni_model_runner.py`

New field added:
```python
ExecuteModelState(
    ...,
    finished_req_ids=finished_req_ids,  # NEW
)
```

**Required action:** Update `_make_execute_model_state()` in `omni_model_runner.py` to include `finished_req_ids`.

### 2.6 `ModelRunnerOutput.with_kv_conn_output_only()` pattern

**Severity: LOW-MEDIUM** | **File affected:** `omni_ar_model_runner.py`

For non-last PP ranks, upstream now uses:
```python
return ModelRunnerOutput.with_kv_conn_output_only(kv_connector_output)
```

**Required action:** Update PP non-last-rank return path.

### 2.7 `intermediate_tensors` no longer in `model_inputs`

**Severity: LOW** | **File affected:** `omni_model_runner.py`

In the current upstream `execute_model`, `intermediate_tensors` is handled separately (via `self.intermediate_tensors` buffer and copy), not passed through `model_inputs` dict.

**Required action:** Remove `"intermediate_tensors": intermediate_tensors` from the `model_inputs` dict in `OmniGPUModelRunner.execute_model()`.

### 2.8 Breakable CUDA graph

**Severity: MEDIUM** | **File affected:** `omni_model_runner.py`

Upstream now uses `cudagraph_manager.run_pw_graph(self.model, model_inputs)` for PIECEWISE mode (which handles both compiled PW graphs and breakable graphs). The old `self.model(**model_inputs)` path no longer covers PIECEWISE.

**Required action:** Update the PIECEWISE branch in `execute_model()` to call `cudagraph_manager.run_pw_graph()` instead of `self.model(**model_inputs)` when in PIECEWISE mode.

### 2.9 New upstream methods requiring pass-through or override

| Method | Required Action |
|--------|----------------|
| `update_pp_decode_requests()` | Call `super()` (already called at start of `execute_model`) |
| `postprocess_num_computed_tokens()` | Call `super()` in Generation runner |
| `_init_kv_zero_meta()`, `post_kv_cache_wake_up()` | No action needed (KV zero init handled by upstream) |
| `reload_weights()`, `update_config()`, `apply_sparse_weight_patches()` | Delegate to V1 runner (upstream already does this) |

---

## 3. Rebase Phases

### Phase 0: Audit & Mechanistic Diff (1 day)

**Goal:** Produce a line-by-line diff between PR #2509's `OmniGPUModelRunner.execute_model()` and current upstream `GPUModelRunner.execute_model()` to identify every divergence.

**Steps:**
1. Check out the PR branch and extract `vllm_omni/worker_v2/` files
2. Diff `OmniGPUModelRunner.execute_model()` against upstream `GPUModelRunner.execute_model()` (lines 1081–1306)
3. Diff `OmniARModelRunner.sample_tokens()` against upstream `GPUModelRunner.sample_tokens()` (lines 1308–1446)
4. Diff `OmniModelState` against upstream `DefaultModelState`
5. Document every divergence with justification (Omni-specific vs stale copy)

### Phase 1: Fix Breaking API Calls (2–3 days)

**Goal:** Make the code compile and pass basic import/unit tests against vLLM HEAD.

**Work items (in dependency order):**

| # | Change | File(s) | Est. |
|---|--------|---------|------|
| 1.1 | Replace `sync_cudagraph_and_dp_padding` with `dispatch_cg_and_sync_dp` | `omni_model_runner.py` | 1h |
| 1.2 | Replace `pp_receive`/`pp_broadcast` with `PPHandler` | `omni_ar_model_runner.py`, `omni_generation_model_runner.py` | 4h |
| 1.3 | Update `postprocess` → `postprocess_sampled` | `omni_ar_model_runner.py` | 0.5h |
| 1.4 | Update `kv_connector.post_forward(scheduler_output)` → `post_forward(finished_req_ids)` | `omni_model_runner.py`, `omni_ar_model_runner.py` | 0.5h |
| 1.5 | Add `finished_req_ids` to `ExecuteModelState` | `omni_model_runner.py` | 0.5h |
| 1.6 | Remove `intermediate_tensors` from `model_inputs` dict | `omni_model_runner.py` | 0.5h |
| 1.7 | Use `run_pw_graph()` for PIECEWISE mode | `omni_model_runner.py` | 1h |
| 1.8 | Update non-last PP rank return to use `with_kv_conn_output_only()` | `omni_ar_model_runner.py` | 0.5h |
| 1.9 | Verify `shutdown()` compat (already conditionally handled) | `omni_model_runner.py` | 0.5h |
| 1.10 | Verify `update_pp_decode_requests()` is called | `omni_model_runner.py` | 0.5h |

### Phase 2: Re-sync `execute_model` With Upstream (3–4 days)

This is the highest-risk phase. `OmniGPUModelRunner.execute_model()` is a ~150-line near-copy of the upstream `execute_model()`. The 31 upstream changes since April must be merged in.

**2.1: Merge upstream structural changes into `execute_model()`**

Key upstream changes that must be incorporated:
- `update_pp_decode_requests()` call at the top
- `dispatch_cg_and_sync_dp` with `need_eager` parameter
- `LorAMapping` dummy run handling for LoRA
- `use_aux_hidden_state_outputs` pattern for hidden state extraction
- `IntermediateTensors` handling pattern for non-first PP ranks
- PIECEWISE mode using `run_pw_graph()` with breakable CUDA graph support

**2.2: Preserve Omni-specific additions**

These Omni-specific behaviors must be preserved in the re-synced `execute_model()`:
1. **Pre-forward `run_preprocess()`** — per-request preprocess + MTP before model forward
2. **Post-forward `run_postprocess()`** — per-request postprocess after model forward
3. **`OmniOutput` unwrapping** — extract `text_hidden_states` + `multimodal_outputs`
4. **`self._last_aux_output` / `self._last_multimodal_outputs`** — store aux outputs for sample_tokens
5. **`_make_execute_model_state()`** — compatibility shim for extra fields
6. **`_needs_capture_tensor_unwrap()`** — conditional FULL graph exclusion for tuple-returning models
7. **`_capture_forward` wrapper** — model forward wrapping during CUDA graph capture

**2.3: Reduce duplication via helper methods**

Rather than maintaining a full copy of `execute_model()`, extract Omni-specific hooks into overridable helper methods:

```python
class OmniGPUModelRunner(GPUModelRunner):
    def execute_model(self, scheduler_output, intermediate_tensors=None,
                      dummy_run=False, skip_attn_for_dummy_run=False,
                      is_profile=False):
        # ... upstream flow ...
        # Pre-forward hook
        if not dummy_run:
            self._omni_pre_forward(input_batch, model_inputs)
        # ... model forward ...
        # Post-forward hook
        if not dummy_run:
            self._omni_post_forward(hidden_states, input_batch)
        # Omni output handling
        self._omni_handle_model_output(model_output)
        # ...

    def _omni_pre_forward(self, input_batch, model_inputs):
        """Omni-specific: per-request preprocess + batched MTP."""
        self.model_state.run_preprocess(input_batch, model_inputs)

    def _omni_post_forward(self, hidden_states, input_batch):
        """Omni-specific: per-request postprocess."""
        self.model_state.run_postprocess(hidden_states, input_batch)

    def _omni_handle_model_output(self, model_output):
        """Omni-specific: extract hidden states from OmniOutput/tuple."""
        # ... unwrapping logic ...
```

This reduces the ~150-line override to ~30 lines of hook calls.

### Phase 3: Re-sync `sample_tokens` With Upstream (2 days)

**3.1: Merge upstream changes**
- PPHandler-based PP flow
- FlashInfer sampler integration
- Speculator MTP target hidden states
- `postprocess_sampled` signature

**3.2: Preserve Omni-specific additions**
1. KV transfer pre-hook (`_handle_kv_transfer_pre`)
2. `OmniOutput` reconstruction (`_reconstruct_raw_model_output`)
3. `postprocess_model_output()` call
4. `_clamp_sampling_prompt_token_ids()` + `compute_logits` monkey-patch
5. `_build_pooler_output_from_cpu()` for per-request pooler slicing
6. `OmniAsyncOutput` for non-blocking D2H with multimodal outputs
7. `OmniModelRunnerOutput` construction

### Phase 4: Update `OmniModelState` Compatibility (1–2 days)

**4.1: Verify `DefaultModelState` changes haven't broken `OmniModelState`**

Key upstream changes to `DefaultModelState`:
- `prepare_attn` with `for_capture` parameter
- `seq_lens_cpu` sync elimination
- `postprocess_state` method
- Hybrid model (Mamba) support

**4.2: Update `OmniModelState.prepare_attn()` override**
- The override already differs (uses actual `max_seq_len`). Verify this is still correct given upstream's `seq_lens_cpu` changes.
- Ensure the `for_capture` parameter is properly handled.

**4.3: Add `postprocess_state()` override if needed**
- `OmniModelState` may need to hook into `postprocess_state()` for intermediate buffer updates.

### Phase 5: Update Tests (2 days)

**5.1: Fix broken unit tests**
- Update mocks for renamed APIs (`dispatch_cg_and_sync_dp`, `PPHandler`, `postprocess_sampled`)
- Fix `_OMNI_ARCHITECTURES` mismatch between source and test (noted in PR review)
- Update `ExecuteModelState` construction in tests to include `finished_req_ids`

**5.2: Add integration test skeletons**
- M-RoPE consistency between V1 and V2
- Pooler output consistency
- KV transfer correctness
- CUDA graph capture for Omni models

### Phase 6: End-to-End Validation (2–3 days)

**6.1: Smoke tests**
- Qwen3-Omni Thinker: offline inference
- Qwen3-Omni Thinker: online serving
- Qwen3-TTS Talker: verify `run_preprocess`/`run_postprocess` works
- Async chunk mode: verify `update_requests` buffer merging

**6.2: Correctness validation**
- V1 vs V2 output consistency (compare logits, pooler_output)
- M-RoPE position correctness
- KV transfer integrity

**6.3: Performance baseline**
- Throughput comparison (V1 vs V2)
- TTFT/TPOT latency
- CUDA graph capture success rate

---

## 4. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | **`execute_model` duplication causes silent drift.** The ~150-line copy misses a subtle upstream change (e.g., tensor lifecycle, stream sync) causing a correctness bug. | Medium | High | Phase 2.3: refactor to hook-based approach that minimizes duplicated lines |
| R2 | **`PPHandler` introduces async complexity.** The new async PP pattern requires consuming results `pp_size` steps later. If vllm-omni's PP handling was synchronous, this creates subtle ordering bugs. | Medium | High | Phase 1.2: carefully analyze the PP flow; add assertions for step ordering |
| R3 | **Breakable CUDA graph breaks Omni capture.** New `run_pw_graph()` path may conflict with `_needs_capture_tensor_unwrap()` and `_capture_forward` wrapper. | Medium | Medium | Phase 2.2: test CUDA graph capture with breakable mode; verify `_exclude_full_graph` still works |
| R4 | **Monkey-patches break on new upstream internals.** Three monkey-patches (`get_rope_state`, `init_model_state`, `compute_logits`) depend on upstream internals that may have changed. | Medium | High | Phase 0: audit all monkey-patch targets against current upstream; add regression tests |
| R5 | **`OmniAsyncOutput` diverges from `AsyncOutput`.** Upstream added `AsyncPoolingOutput` and changed async copy patterns. | Low | Medium | Phase 3.2: diff `OmniAsyncOutput` against current `AsyncOutput`; consider inheriting instead of copying |
| R6 | **`update_pp_decode_requests()` conflicts with Omni request lifecycle.** The new PP decode request update may not account for Omni's intermediate buffer. | Low | Medium | Phase 2.2: verify `update_requests()` buffer merging still works after PP decode update |

---

## 5. Timeline

```
Week 1: Phase 0 (Audit) + Phase 1 (Fix Breaking APIs)
Week 2: Phase 2 (Re-sync execute_model) + Phase 3 (Re-sync sample_tokens)
Week 3: Phase 4 (OmniModelState) + Phase 5 (Tests)
Week 4: Phase 6 (E2E Validation) + Buffer
```

**Total estimated effort: 12–18 days** (assuming one developer full-time)

---

## 6. Appendix: Key Upstream Commits That Must Be Incorporated

These are the 31 commits on `model_runner.py` since April 2026, annotated with risk to vllm-omni:

| Commit | Description | Risk |
|--------|-------------|------|
| `ceb0111a9` | Gemma4 MTP support | Low |
| `91945b6e4` | Warmup & capture with different attention states | Medium |
| `e15f20258` | Avoid pipeline parallel bubbles | **High** |
| `da107a59e` | Enable MRV2 for Llama/Mistral dense models | Low |
| `8a9eb4080` | Zero freshly allocated KV blocks for hybrid + fp8 | Low |
| `27fa5aa3b` | Support breakable CUDA graph | **High** |
| `7e53283b1` | Cleanup KVConnector handling with PP + fix MRV2 | **High** |
| `1223732dd` | Support kernel block size in hybrid model | Low |
| `8c94938cf` | Fix KV connector handling in spec decode | Medium |
| `47d4407d7` | Support sharing kv cache layers | Low |
| `9640970de` | Fix lora Triton CUDA error | Low |
| `fba010dd7` | Fix KVCache tensor kernel_block_size dim | Low |
| `f5d3dc711` | Support update_config | Low |
| `6147c7022` | Support reload weights (sleep mode) | Low |
| `016259660` | FP32 gumbel sampling | Low |
| `9af6a5ed7` | Fix seq_lens_cpu_upper_bound | Medium |
| `7a08b34fb` | Support qwen35 / mamba hybrid model | Medium |
| `e6ff3e9c8` | Add shutdown() method | Low |
| `526927be9` | Fix v2 compile counter | Low |
| `51fda1ba4` | Fix block table IMA issue | Low |
| `4c7c69b4e` | Skip attention metadata rebuild before draft prefill | Low |
| `e1e4646b0` | Rebuild attn metadata between draft decode steps | Low |
| `51295793a` | Add logprob_token_ids support | Low |
| `fe5b4e0fe` | Apply synthetic mode to probabilistic rejection sampler | Low |
| `d7af6b34d` | Logprob dtype int64/int32 fix | Low |
| `3b6a20478` | DSV4 lazy attention during cudagraph capture | Low |
| `39bba710b` | Fix default-stream CG capture in P/W LoRA | Medium |
| `ec8d60bea` | Use FlashInfer sampler | Medium |
| `ffce72c04` | Fix CohereASRDecoder embed_input_ids | Low |
| `0bae1d384` | DFlash spec decode | Low |
| `2c27c294c` | Fix mrv2 mm lora issue | Low |

---

## 7. Appendix: Complete File Change List

Files in `vllm_omni/worker_v2/` that need updating:

| File | Lines | Breaking Changes |
|------|-------|-----------------|
| `omni_model_runner.py` | 372 | #2.2, #2.4, #2.5, #2.7, #2.8 |
| `omni_ar_model_runner.py` | 510 | #2.1, #2.3, #2.4, #2.6 |
| `omni_generation_model_runner.py` | 394 | #2.1, #2.4 |
| `model_states/omni_model_state.py` | 513 | #4.1, #4.2, #4.3 |
| `model_states/intermediate_buffer.py` | 147 | None |
| `model_states/__init__.py` | 49 | None |
| `model_states/plugin.py` | 42 | None |
| `model_states/models/__init__.py` | 0 | None |
| `forward_compat.py` | 33 | May need update |
| `outputs.py` | 5 | None |
