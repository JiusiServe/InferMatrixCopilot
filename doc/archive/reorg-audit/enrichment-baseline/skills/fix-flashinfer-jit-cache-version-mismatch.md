---
name: fix-flashinfer-jit-cache-version-mismatch
description: vLLM 0.25 engine/diffusion workers die at startup with "flashinfer-jit-cache version X does not match flashinfer version Y" — a stale flashinfer-jit-cache package in the venv; uninstall it (upstream pins only flashinfer-python + flashinfer-cubin).
trigger: RuntimeError "flashinfer-jit-cache version ... does not match flashinfer version" in worker/engine startup logs; every TP worker dies, orchestrator init fails with EOFError; also appears as WARNING "FlashInfer is unavailable; falling back" before the hard failure in device-communicator import.
modules: [worker_runner, model_executor]
status: active
created_at: 2026-07-12
last_used_at: 2026-07-12
run_count: 1
---

## Diagnose
1. Worker traceback ends in `flashinfer/jit/env.py: _get_aot_dir` raising
   `RuntimeError: flashinfer-jit-cache version (A) does not match flashinfer version (B)`.
   The import chain is vLLM 0.25's `cuda_communicator.py` → `flashinfer_all_reduce` →
   `import flashinfer.comm`, so ALL TP workers die together and the engine reports
   `Orchestrator initialization failed` / `Rank 0 scheduler is dead` / EOFError.
2. Confirm the mismatch: `pip list | grep -i flashinfer` — three packages where
   `flashinfer-jit-cache` version ≠ `flashinfer-python` version.
3. Confirm what upstream expects: `git show <vllm-tag>:requirements/cuda.txt | grep flashinfer`
   — v0.25.0 pins `flashinfer-python==0.6.13` and `flashinfer-cubin==0.6.13` only;
   there is NO flashinfer-jit-cache pin. A jit-cache package in the venv is a stale
   leftover from an earlier manual install.

## Fix
Uninstall the stale package — do NOT bypass with FLASHINFER_DISABLE_VERSION_CHECK
(that leaves mismatched cached kernels in play):

```bash
/rebase/.venv/bin/pip uninstall -y flashinfer-jit-cache
/rebase/.venv/bin/python -c "import flashinfer.comm; print('ok', flashinfer.__version__)"
```

Without jit-cache, flashinfer uses the matching `flashinfer-cubin` package (same as
the CI docker image), so kernel selection matches CI.

## Verification
`python -c "import flashinfer.comm"` succeeds, and a previously-failing engine
startup (e.g. `examples/offline_inference/hunyuan_image3/end2end.py` with a TP>1
deploy config) reaches "Loading safetensors" and completes. Verified 2026-07-12
during the HunyuanImage3 golden re-baseline on vLLM 0.25.0rc4.dev1+gdd10e03f9.

## Anti-patterns
- Setting `FLASHINFER_DISABLE_VERSION_CHECK` to silence the error — mismatched
  precompiled kernels may then be loaded, and numerics can diverge from CI.
- Pinning flashinfer-jit-cache to match by hand — upstream doesn't ship/pin it for
  this stack; the cubin package is the supported artifact and drifts less.
- Reinstalling vllm/vllm-omni — the engine code is fine; only the extra package is stale.
