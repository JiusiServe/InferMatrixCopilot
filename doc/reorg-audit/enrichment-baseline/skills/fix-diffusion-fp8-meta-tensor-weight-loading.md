---
name: fix-diffusion-fp8-meta-tensor-weight-loading
description: Fix "Cannot copy out of meta tensor" crash when loading FP8 online-quantized diffusion models after rebasing onto newer upstream vLLM (uses_meta_device online quant)
trigger: Diffusion worker startup crashes with "NotImplementedError: Cannot copy out of meta tensor; no data! Please use torch.nn.Module.to_empty()" at diffusers_loader.py in _process_weights_after_loading; cascades to EOFError in multiproc_executor and "Server processes exited with code 1 before becoming ready". Hits FP8 quantization tests (test_single_stage_qwen_image_fp8, test_bagel_fp8_generates_image) and fp8 vae_patch_parallel diffusion serving. Appears only AFTER rebasing to a newer upstream vLLM, not on the older-vLLM main branch.
modules: [diffusion_model_loader, quantization, worker_runner]
status: active
created_at: 2026-07-08
last_used_at: 2026-07-11
run_count: 5
---

## Diagnose
1. Symptom: a diffusion FP8 test (or fp8 serving path) fails; the pytest-level error is `RuntimeError: Server processes exited with code 1 before becoming ready`. The REAL crash is in the spawned `DiffusionWorker` subprocess — grep the job log for `Traceback` / `meta tensor`:
   ```
   File ".../vllm_omni/diffusion/model_loader/diffusers_loader.py", line ~416, in _process_weights_after_loading
       module.to(target_device)
   NotImplementedError: Cannot copy out of meta tensor; no data! Please use torch.nn.Module.to_empty() ...
   ```
   Parent then shows `multiproc_executor ... reader.recv() -> EOFError` and `Orchestrator initialization failed`.
2. Confirm it is a rebase regression: the SAME test PASSES on vllm-omni `main`'s nightly (which tracks an older vLLM). Use the Buildkite API to compare — main nightly (pipeline `vllm-omni`, source=schedule, NIGHTLY=1) vs the align build (pipeline `vllm-omni-rebase`).
3. Root cause: newer upstream vLLM online-quant linear methods set `uses_meta_device = True` (`vllm/model_executor/layers/quantization/online/fp8.py`) and allocate weights on the `meta` device, materializing them just-in-time via the layerwise online-process loader (`initialize_online_processing`) as each layer finishes loading. "Straggler" layers (padding / partially-loaded) stay on `meta`. vllm-omni's `_process_weights_after_loading` did a blanket recursive `module.to(target_device)`, which cannot move meta tensors. Model-specific: Z-Image FP8 materializes fully (passes); Qwen-Image / BAGEL FP8 leave stragglers (crash).
4. Note: `_process_weights_after_loading` iterates every module whose `quant_method` isinstance `QuantizeMethodBase` — that INCLUDES unquantized linears (`UnquantizedLinearMethod`), but only meta-device (online-quant) params trigger the crash.

## Fix
In `vllm_omni/diffusion/model_loader/diffusers_loader.py`, `_process_weights_after_loading`, mirror upstream vLLM's `base_loader` contract:
1. Before the per-module loop, materialize online-quant stragglers (only when online quant is actually used, so older vLLM without this module is unaffected):
```python
if self._has_online_quant(model):
    from vllm.model_executor.model_loader.reload.layerwise import finalize_layerwise_processing
    finalize_layerwise_processing(model, model_config=None)  # None ok: only used for vLLM Attention/MLA layers, which DiT has none of
```
with a helper:
```python
@staticmethod
def _has_online_quant(model):
    for m in model.modules():
        if getattr(getattr(m, "quant_method", None), "uses_meta_device", False):
            return True
    return False
```
2. **GATE the meta-safe move to online quant ONLY.** For online-quant modules, replace the blanket `module.to()` with a per-parameter move mirroring `device_loading_context` (move only real, non-meta params; restore after). For every other module keep the ORIGINAL whole-module `module.to(target_device)` — it is FSDP/HSDP-aware and non-quant modules never have meta params:
```python
has_online_quant = self._has_online_quant(model)   # computed once, before the loop
...
for _, module in model.named_modules():
    quant_method = getattr(module, "quant_method", None)
    if quant_method is None or not isinstance(quant_method, QuantizeMethodBase):
        continue
    if has_online_quant:
        original_devices = {}
        for name, param in module.named_parameters():
            if param.device.type != "meta" and param.device != target_device:
                original_devices[name] = param.device
                param.data = param.data.to(target_device)
        quant_method.process_weights_after_loading(module)
        for name, param in module.named_parameters():
            if name in original_devices:
                param.data = param.data.to(original_devices[name])
    else:
        # original FSDP/HSDP-aware path (no meta params possible here)
        module_device = next(module.parameters(), None)
        module_device = module_device.device if module_device is not None else None
        needs_move = module_device != target_device
        if needs_move:
            module.to(target_device)
        quant_method.process_weights_after_loading(module)
        if needs_move:
            module.to(module_device)
```

## Verification
- Isolated mechanics: a module with one cpu param + one `torch.empty(..., device="meta")` param runs the per-param move loop with NO `NotImplementedError`, real param moves+restores, and `module.to()` on the meta param still raises (proves the old path was the bug).
- End-to-end: rerun the nightly `Quantization Test` (H100 + L4) and `Diffusion ... Qwen-Image` (fp8 vae_patch_parallel_2). They must go green AND the tests' own image assertions (valid PIL image / SSIM) must pass — a wrong "materialize with garbage" fix would fail the accuracy assertion, not the crash.

## Anti-patterns
- Do NOT apply the per-parameter `param.data = param.data.to(...)` move UNCONDITIONALLY (to every quant_method module, quant or not). It breaks the FSDP/HSDP path: after `apply_hsdp_to_model` params are sharded DTensors whose storage cannot be cross-device reassigned via `.data`, raising `RuntimeError: Attempted to set the storage of a tensor on device "cuda:0" to a storage on different device "cpu"` at load time (regressed nightly `test_zimage[layerwise_hsdp]`). Meta params ONLY come from online quant, so GATE the per-param path on `_has_online_quant(model)` and leave the FSDP-aware `module.to()` for everything else.
- Do NOT "fix" by calling `module.to_empty(device=target_device)` — that allocates UNINITIALIZED memory, silently producing garbage weights/images that may still pass a crash check but fail accuracy (SSIM) tests.
- Do NOT revert the Dockerfile.ci cu130/torch-2.11.0 environment to match main to make it pass — main runs the OLD vLLM (v0.24.0 tag), the align branch intentionally targets a newer upstream commit (585 commits ahead). Reverting the environment abandons the rebase target; the fix belongs in the loader code.
- Do NOT import `finalize_layerwise_processing` at module top-level unconditionally — older vLLM may not have `reload.layerwise`; import lazily inside the `_has_online_quant` guard.
