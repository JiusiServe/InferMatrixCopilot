Good. I have everything I need. Here's my review.

---

## BLOCKER Scan

| Category | Result |
|----------|--------|
| Correctness | PASS |
| Reliability/Safety | PASS |
| Breaking Changes | PASS (kwargs-only params with defaults, backward-compatible) |
| Test Coverage | PASS (new test covers SP=1, SP=2 odd/even, SP=4 with control) |
| Documentation | PASS (inline docstring on the new method) |
| Security | PASS |

**Verdict:** Clean bugfix. No blocking issues. Recommended: APPROVE.

---

### Review comments

**`vllm_omni/diffusion/models/cosmos3/transformer_cosmos3.py:1395`** — The lazy import inside the method body is consistent with the existing `_get_ulysses_state` pattern, so this isn't a blocking issue. But if there's appetite to clean this up later, these could both be top-level imports behind a `TYPE_CHECKING` guard or just imported unconditionally (the module is already imported at the top of `pipeline_cosmos3.py`). Not worth blocking this PR on.

**`vllm_omni/diffusion/models/cosmos3/pipeline_cosmos3.py:3081-3085`** — Moving `video_shape` computation before `_prepare_sound_latents` is safe since `latents` is already available. The `sp_num_vision_items` defaults to 1, which is correct here since the pipeline rejects transfer+sound combinations earlier in `forward()`.

---

**Summary:** The fix correctly pads sound latent frames so the joint (vision+sound) sequence is divisible by `ulysses_degree`. The pad computation mirrors the existing `_validate_gen_sequence_parallel` token-counting logic. The extra frames are trimmed back to the requested duration in `_decode_sound_latents`. No-op when SP is inactive (`ulysses_size <= 1`). The test covers the key cases.