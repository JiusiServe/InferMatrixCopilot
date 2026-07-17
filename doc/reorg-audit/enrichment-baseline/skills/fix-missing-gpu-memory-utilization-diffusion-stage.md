---
name: fix-missing-gpu-memory-utilization-diffusion-stage
description: Add gpu_memory_utilization to diffusion stage in CI config when sharing GPU with LLM stage to prevent CUDA OOM
trigger: A distributed test fails with CUDA OOM during model loading of a multi-stage model (e.g., Bagel) where stages share the same GPU. The OOM traceback shows torch.OutOfMemoryError during MergedColumnParallelLinear.create_weights or similar weight allocation in the diffusion stage.
modules: [input_output, model_config]
status: active
created_at: 2026-06-16
last_used_at: 2026-07-11
run_count: 32
---

## Diagnose

1. Check if the CI test config has `gpu_memory_utilization` set for ALL stages.
2. If stage 1 (diffusion) has no `gpu_memory_utilization`, it defaults to 0.92 (92%).
3. With stage 0 using 45% and stage 1 using 92% on the same GPU, total > 100% causes OOM.
4. The diffusion stage loads BOTH the diffusion model AND an LLM internally (e.g., Qwen2MoT), consuming ~27.5 GiB for weights alone.
5. Verify: check `tests/.ci_generated/bagel.yaml` or the `_CI_OVERLAYS` in `tests/helpers/stage_config.py`.

## Fix

Add `gpu_memory_utilization: 0.5` to stage 1 in both:
1. `tests/helpers/stage_config.py` - the `_CI_OVERLAYS["bagel"]` dict (source template)
2. `tests/.ci_generated/bagel.yaml` - the generated config (regenerate or edit directly)

```python
# In _CI_OVERLAYS["bagel"]:
{
    "stage_id": 1,
    "max_num_seqs": 1,
    "gpu_memory_utilization": 0.5,  # ADD THIS
},
```

```yaml
# In generated YAML:
- stage_id: 1
  max_num_seqs: 1
  gpu_memory_utilization: 0.5  # ADD THIS
```

## Verification
```bash
python -m pytest tests/distributed/omni_connectors/test_bagel_shared_memory_connector.py -x -q --no-header
```

## Why 0.5
- GPU total: ~140 GiB (L20X)
- Stage 0 uses 45% = ~63 GiB
- Stage 1 model weights: ~27.5 GiB
- 50% = ~70 GiB provides ample margin above model weight baseline
- Conservative enough to leave room for stage 0 on any GPU
