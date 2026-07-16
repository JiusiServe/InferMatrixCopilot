```markdown
### Findings

1. **transformer_cosmos3.py:1376–1400** [normal] — Add a docstring for `sound_latent_frames_for_sequence_parallel` that explains `video_shape` must be in VAE‑latent space (not pixels), that `_pad_to_patch_size` further patches it, and that the padded frames are real diffusion tokens (not masked) so SP output diverges from non‑SP. This clarifies the method’s non‑obvious assumptions and side effect.

2. **transformer_cosmos3.py:1382–1385** [nit] — Update the inline comment to explicitly mention that `num_vision_items` accounts for transfer‑control vision items, not just a single vision token set. This avoids confusion when the comment says *“the base is just the vision tokens”* while the parameter already handles multiple vision items.

3. **pipeline_cosmos3.py:3078–3081** [nit] — Add a brief comment noting that `sp_num_vision_items` defaults to 1 because sound+transfer is rejected at the pipeline level, so the parameter is intentionally left at its default. This documents why the value is never overridden today.

4. **test_cosmos3_transformer.py:350** [unverified] — Consider asserting the concrete padded value (e.g., 100 for the given parameters) in addition to the divisibility check, to guard against accidental changes to the padding formula.

### Verdict
APPROVE (the requested documentation and test improvements can be addressed non‑blockingly).
```