## Review of PR #4678 — `[BugFix][Cosmos3] Pad sound latents so video+sound runs under sequence parallelism`

**Author:** lishunyang12 · **Status:** MERGED · **Base:** `main`
**Gates:** DCO ✅ · pre-commit ✅ · build 3.11/3.12 ✅
(No GitHub post made — output only, as requested.)

---

### Blocker scan

| Category | Result |
|---|---|
| Correctness | PASS |
| Reliability/Safety | PASS |
| Breaking Changes | PASS (no-op when SP inactive; audio duration preserved) |
| Test Coverage | PASS (unit test covers SP-inactive, odd→even, already-divisible, ulysses=4) |
| Documentation | PASS (behavior caveat documented inline) |
| Security | PASS |

### What I verified

- **The padding arithmetic matches the real packed GEN sequence.** The validator `_validate_gen_sequence_parallel` gates on `hidden_gen.shape[1] = s_control + s_video + s_action + s_sound`. For the sound case, control+sound is rejected, action+sound is rejected, so `s_gen = s_video + s_sound`. The new method's `base + sound_frames = (t·hp·wp) + sound_frames` equals exactly that, so the padded count genuinely satisfies the validator. `t` is used un-patchified, which is correct — `latent_patch_size` is spatial-only (`patchify` reshapes `[B,C,t,h,w] → [B, t·hp·wp, ...]`).
- **The action-free assumption is actually enforced**, not just assumed — `forward` raises `"Cosmos3 action+sound joint generation is not supported"` (`pipeline_cosmos3.py:2911`). Good, since the padding formula omits action tokens.
- **Requested duration is preserved.** The extra padded frames inflate the latent tensor, but decode trims the waveform back to the un-padded `target_audio_samples` (`pipeline_cosmos3.py:1762-1763`). The discarded 2nd return value (`sound_latents, _ =`) is redundant with `sound_latents.shape[-1]`, so dropping it loses nothing.
- **Non-bit-exactness with non-SP is honestly documented** in the method comment — padded frames pass through attention and perturb the kept ones. Acceptable and disclosed.

### Recommended verdict: **APPROVE**

Clean, correctly-scoped bugfix with a focused regression test. No blocking issues.

### Optional non-blocking comment

**`vllm_omni/diffusion/models/cosmos3/transformer_cosmos3.py:1381`**
> `num_vision_items` is always 1 at the only call site (control+sound is rejected in `forward`), so the `ulysses=4, num_vision_items=2` test branch exercises a path production never hits. Fine to keep for generality, but worth a one-line note that it's forward-looking rather than currently reachable.

This is a nit, not a merge blocker — I'd have approved without it.