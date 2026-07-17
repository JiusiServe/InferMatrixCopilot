---
name: fix-voxcpm2-l4-oom-after-rebase
description: VoxCPM2 CI OOM on L4 (24GB) — canonical skill. KV cache is now pinned via kv_cache_memory_bytes in voxcpm2.yaml; do NOT resume the old gpu_memory_utilization decrement ratchet.
trigger: test_voxcpm2_* exits with status -1 on L4 (24GB). CUDA graphs captured / PREFILL succeeds, then 30-60s silence during decode, then 'Received cancellation signal, interrupting'. No Python traceback.
modules: [worker_runner]
status: active
created_at: 2026-06-07
last_used_at: 2026-07-11
run_count: 30
---

## Symptom signature

- Exit code -1 (killed by signal / Docker OOM), NOT a Python traceback.
- Log shows `CUDA Graph captured for scaffold (batch_size=N)`, all prefill
  completes, then ~30-60s silence during decode, then
  `Received cancellation signal, interrupting`.
- The OOM spike comes from the VoxCPM2 diffusion side-path (CFM solver,
  batched VAE decode, LocDiT) which allocates **outside** vLLM's KV-cache
  accounting during decode.

## Current state of the fix (read this before changing anything)

`vllm_omni/deploy/voxcpm2.yaml` now pins the KV cache directly:

- `kv_cache_memory_bytes: 6442450944` (6 GiB) — right-sized for
  max_num_seqs(2) * max_model_len(4096); the rest of VRAM stays free for the
  diffusion side-path. Peak ~13 GiB on any card.
- `max_num_seqs: 2`, `gpu_memory_utilization: 0.70`, `vae_decode_every: 1`,
  `enforce_eager: true`, prefix caching off.

This replaced the 2026-06-04..06-09 era of decrementing
`gpu_memory_utilization` each rebase (0.90→0.85→0.80→0.75→0.70→0.65 and back).
With `kv_cache_memory_bytes` set, `gpu_memory_utilization` no longer controls
the KV cache size, so decrementing it again is pointless.

## Anti-pattern (DO NOT DO THIS)

- Do NOT reduce `gpu_memory_utilization` by another 0.05 "one more time".
  That ratchet ran 5+ times without fixing the root cause and is superseded
  by the KV-cache pin.

## Diagnose / Fix if it OOMs again despite the pin

1. Confirm the yaml still has `kv_cache_memory_bytes` — a rebase conflict may
   have dropped it. If dropped, restore it (see Current state above).
2. Check whether the vLLM bump increased baseline weights/activations: compare
   `Model loading took N GiB` and free-VRAM lines against the last passing
   run's log (`rebase_logs/runs/<prev>/tests/00_tts_voxcpm2_test.log`).
3. If the diffusion side-path itself grew, the levers are (in order):
   `max_num_seqs` 2→1, disable `enable_batched_vae_decode`, or lower
   `kv_cache_memory_bytes` — each trades throughput; record measurements in
   debug memory rather than guessing.
4. Check `search_debug_memory(keyword="voxcpm2_l4_oom")` for history.
