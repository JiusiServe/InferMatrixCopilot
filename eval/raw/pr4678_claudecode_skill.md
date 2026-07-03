Now I have all the context I need. Let me compile the complete review.

---

## PR #4678 Review — [BugFix][Cosmos3] Pad sound latents so video+sound runs under sequence parallelism

**Author:** lishunyang12 | **State:** MERGED | **+65/−7** across 4 files

### Gate Check

| Check | Status |
|-------|--------|
| DCO | ✅ SUCCESS |
| pre-commit | ✅ SUCCESS |
| Buildkite (main) | ✅ SUCCESS |
| Buildkite (intel) | ✅ SUCCESS |
| Buildkite (npu) | ✅ SUCCESS |
| AMD CI | ❌ FAILURE — pre-existing; main pipeline passes |

### BLOCKER Scan

| Category | Result |
|----------|--------|
| Correctness | PASS |
| Reliability/Safety | PASS |
| Breaking Changes | PASS |
| Test Coverage | PASS |
| Documentation | PASS |
| Security | PASS |

### Analysis

The bug is real: under Ulysses sequence parallelism, the packed GEN sequence length must be divisible by `ulysses_degree`. Sound token counts are `ceil(duration × latent_fps)`, frequently making `vision + sound` non-divisible and crashing video+sound generation.

The fix pads sound latents to alignment, trims on decode. The new `sound_latent_frames_for_sequence_parallel` method on `Cosmos3VFMTransformer` is clean — early-returns for no-SP (`ulysses_size <= 1`) and zero/negative frames, then computes `pad = (-(base + sound_frames)) % ulysses_size`. The padding math is correct.

The `_prepare_sound_latents` signature change is backward-compatible: new params are keyword-only (`*`) with safe defaults. The one production caller in `forward()` passes `sp_video_shape=video_shape` and relies on the default `sp_num_vision_items=1`, which is correct because the pipeline explicitly rejects both `transfer + sound` (L2907) and `action + sound` (L2911). The test mock at `test_cosmos3_pipeline.py:1401` correctly accepts `**kwargs`.

### Non-blocking Observations

1. **`vllm_omni/diffusion/models/cosmos3/pipeline_cosmos3.py:1672`** — `sp_num_vision_items` is never passed by any production caller; always defaults to 1. This is forward-looking and harmless, but if it's expected to stay at 1 indefinitely, consider documenting why (or removing it until needed).

2. **`tests/diffusion/models/cosmos3/test_cosmos3_transformer.py:350`** — The assertion `(2 * 192 + padded) % 4 == 0` is correct but `192` is a magic number (`t * hp * wp = 3*16*16 = 768`; per-rank slice under ulysses=4). A brief comment would help the next reader.

3. **`vllm_omni/diffusion/models/cosmos3/transformer_cosmos3.py:1392`** — The `from vllm_omni.diffusion.distributed.parallel_state import get_ulysses_parallel_world_size` import is inside the method body. If this is for circular-import avoidance (common in vllm), it's fine; otherwise consider moving it to the top.

### Recommended Verdict

**APPROVE** — no blockers. Clean targeted fix with adequate tests and backward-compatible API changes.