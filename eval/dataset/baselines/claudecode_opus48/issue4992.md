I've confirmed the report against the code. Here is my maintainer answer.

---

## Answer (as maintainer)

Thanks @zhangj1an — this is an excellent write-up, and the root-cause analysis is **correct**. I can confirm every claim against the tree at `9ceca4ec8`, and I want to add two details that strengthen the case for fixing it at the base-layer level.

### Confirmed root cause

`CustomOp.dispatch_forward` binds the forward implementation **once at init time** from the active platform, with no notion of per-call tensor device (`vllm_omni/diffusion/layers/custom_op.py:19-31`, selecting `forward_npu` at line 24-25). So on an Ascend machine every `RMSNorm`/`RMSNormVAE` instance is permanently wired to `forward_npu`, regardless of where the input tensor actually lives.

`RMSNorm.forward_npu` (`vllm_omni/diffusion/layers/norm.py:110-118`) and `RMSNormVAE.forward_npu` (`norm.py:173-190`) then call `torch_npu.npu_rms_norm(...)` unconditionally. That op is registered only for the `PrivateUse1` (NPU) backend, so a CPU tensor is rejected with the `NotImplementedError` you quoted. Nothing about this is Cosmos3-specific — these are generic layers under `diffusion/layers/`.

### Two things worth adding

1. **The Cosmos3 path proves the fix belongs in the base class, not the model.** The Cosmos3 transformer doesn't use the shared `RMSNorm` directly — it defines a *local* subclass (`vllm_omni/diffusion/models/cosmos3/transformer_cosmos3.py:44-51`) whose whole purpose is to force the FP32 native path:

   ```python
   class RMSNorm(_VllmRMSNorm):
       """Cosmos3-local RMSNorm that uses the FP32 native implementation."""
       def forward_cuda(self, x): return self.forward_native(x)
       def forward_hip(self, x):  return self.forward_native(x)
   ```

   It overrides `forward_cuda`/`forward_hip` but **not** `forward_npu`, so on NPU it silently inherits the unguarded op and crashes — exactly the 5 failing tests. Patching Cosmos3 alone (or folding it only into the Cosmos3-Super recipe) would leave the same landmine for every other model that touches these layers. The guard should live in `norm.py`.

2. **The CUDA path is already guarded; NPU just missed it.** `forward_cuda` wraps the fused kernel in `try/except → forward_native` (`norm.py:94-97`), and `forward_xpu`/`RMSNormVAE.forward_cuda/_hip/_xpu` all delegate to `forward_native`. As you noted, `LayerNorm.forward_npu` also falls back (`norm.py:42-54`). `forward_npu` for `RMSNorm`/`RMSNormVAE` is the one code path with no fallback at all — so this is closing a consistency gap, not introducing new behavior.

### On the proposed fix — endorsed, with a note

The device guard is the right minimal fix, and `forward_native` is a numerically valid substitute for both layers:
- `RMSNorm.forward_native` (`norm.py:126-135`) does the standard last-dim RMS in fp32 — same reduction axis as `npu_rms_norm`.
- `RMSNormVAE.forward_native` (`norm.py:198-213`) uses `F.normalize(...) * scale * gamma`, i.e. `x / (‖x‖₂/√dim) = x / RMS(x)`, which equals the transpose-then-`npu_rms_norm` result at line 182-186, and it applies `gamma`/`bias` identically. So falling back on CPU is safe.

`x.device.type != "npu"` is the correct predicate (torch_npu exposes Ascend tensors as device type `"npu"`). Keep the `import torch_npu` *after* the guard as you wrote it.

Two small suggestions when you open the PR:
- Guard on the *device*, not just fall back on any non-NPU tensor, so a genuinely misplaced tensor on NPU still takes the fast op. Your `if x.device.type != "npu": return self.forward_native(x)` already does exactly this — 👍.
- Add a tiny CI regression test that instantiates `RMSNorm`/`RMSNormVAE` and pushes a **CPU** tensor through them under the NPU platform plugin, asserting it matches `forward_native`. That's what actually keeps the Cosmos3 unit tests green on Ascend runners and prevents a future subclass from regressing this.

### Re: fold into Cosmos3-Super or keep separate?

**Keep it separate.** This is a generic diffusion-layer + CI correctness fix that unblocks NPU unit testing for many models; it shouldn't be gated behind the Cosmos3-Super recipe's review/merge cadence. Land the `norm.py` guard as its own small PR (tagged `bug`/`NPU`/`CI`), then Cosmos3-Super can just build on top of a fixed base. Your triage of the neighboring issues (#4247 is a distinct CUDA IMA on the LTX path, #1030 is the underlying init-time-dispatch design, #4340 is the Cosmos3 tracker) is accurate — this is a new, standalone bug, not a duplicate.

Marking as a valid, confirmed bug (already reproduced by @FayeSpica on A3). Happy to review the PR.