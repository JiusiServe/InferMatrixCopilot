I now have everything needed. Let me write the maintainer response.

---

Thanks for the detailed logs — this is a **configuration issue, not a bug in vllm-omni**, and it's easy to fix.

## Root cause

The failing assertion is here:

```
vllm_omni/worker/gpu_ar_worker.py:72
    assert self.local_rank < torch.accelerator.device_count(), (
        f"DP adjusted local rank {self.local_rank} is out of "
        f"bounds for {torch.accelerator.device_count()} devices."
    )
```

It fires in **stage 1 (the Talker)**: the stage is being launched with **`tensor_parallel_size=4`** (so it spawns workers with local ranks 0–3), but you only assigned it **one GPU** (`"devices": "0"`), so ranks 1/2/3 have no device → *"DP adjusted local rank 3 is out of bounds for 1 devices."*

Why is stage 1 running TP=4 when you never asked it to? Because **`--tensor-parallel-size 4` is a *global* engine arg, and global args are applied to *every* stage** unless that stage explicitly overrides them. You can see this in the override-merge logic:

```
vllm_omni/config/stage_config.py:76
    for key, value in cli_overrides.items():
        ...
        match = _STAGE_OVERRIDE_PATTERN.match(key)   # matches "stage_1_..."
        if match is not None:
            if override_stage_id == stage_id ...:
                result[param_name] = value           # per-stage override
            continue
        result[key] = value                          # GLOBAL arg → applied to ALL stages
```

`--stage-overrides` entries become `stage_<id>_<key>` keys (`vllm_omni/entrypoints/utils.py:349-352`). Your stage-1/stage-2 blocks only set `devices` and `gpu_memory_utilization` — you never set `tensor_parallel_size` for them — so they inherit the global TP=4 and try to shard a single-GPU stage across 4 ranks.

For reference, the Talker (stage 1) and Code2Wav (stage 2) are **TP=1, single-GPU stages by design** in the default deploy config; only the Thinker (stage 0) is meant to be sharded:

```
vllm_omni/deploy/qwen3_omni_moe.yaml:25   # stage 0 → devices "0"  (TP defaults to 1)
                                    :37   # stage 1 → devices "1"  (TP defaults to 1)
                                    :52   # stage 2 → devices "1"  (TP defaults to 1)
```

This also explains all three of your commands failing:
- **cmd 1 / cmd 3** (with `--stage-overrides`): stage 0 has 4 devices so it's fine, but stages 1 & 2 get TP=4 on 1 device → crash (exactly what @amy-why-3459's device-mapping diff shows).
- **cmd 2** (no `--stage-overrides`): stage 0 falls back to the deploy default `devices: "0"` (1 GPU) but still inherits global TP=4 → same crash, now on stage 0.

## The fix

Set `tensor_parallel_size` **explicitly per stage** and **drop the global `--tensor-parallel-size 4`** (leaving it in is redundant and only re-introduces the leak for any stage you forget to override):

```bash
vllm serve /data/model/Qwen3-Omni-30B-A3B-Instruct \
  --omni \
  --served-model-name qwen3-omni-30b-a3b-instruct \
  --trust-remote-code \
  --max-model-len 16384 \
  --stage-overrides '{
    "0": {"tensor_parallel_size": 4, "devices": "0,1,2,3", "gpu_memory_utilization": 0.8},
    "1": {"tensor_parallel_size": 1, "devices": "0", "gpu_memory_utilization": 0.1},
    "2": {"tensor_parallel_size": 1, "devices": "1", "gpu_memory_utilization": 0.1}
  }' \
  --host 0.0.0.0 --port 8091
```

That gives you: Thinker sharded TP=4 across GPUs 0–3, Talker on GPU 0 (TP=1), Code2Wav on GPU 1 (TP=1) — the layout your overrides were clearly aiming for. Your memory split is fine (device 0: 0.8+0.1, device 1: 0.8+0.1).

Note: `--enable-prefix-caching` is not related to this crash (the deploy config keeps prefix caching off for these stages anyway), so you can add it back if you want.

## Simpler alternative

If you don't need a custom device layout, just let the registry-loaded deploy config place the stages for you and only bump the Thinker's TP:

```bash
vllm serve /data/model/Qwen3-Omni-30B-A3B-Instruct --omni --port 8091 \
  --trust-remote-code \
  --stage-overrides '{"0": {"tensor_parallel_size": 4, "devices": "0,1,2,3"}}'
```

Or run one stage per process (`--stage-id 0/1/2` with `CUDA_VISIBLE_DEVICES`), as documented in `recipes/Qwen/Qwen3-Omni.md` — that sidesteps global-arg leakage entirely because each process is a single stage.

## Takeaway for maintainers

This is at least the second report of a global parallelism arg silently leaking into single-GPU auxiliary stages. It would be worth emitting a **clear startup error** when a stage ends up with `tensor_parallel_size > len(devices)` (naming the stage and the offending value) instead of surfacing the low-level `local_rank ... out of bounds` assertion from the worker — the current message gives users no hint that the fix is a per-stage `tensor_parallel_size`. I'd suggest keeping this issue open as a UX/validation improvement, but the user's immediate problem is resolved by the corrected command above.