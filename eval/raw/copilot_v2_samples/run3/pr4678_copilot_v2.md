```markdown
transformer_cosmos3.py:1378-1385 [normal] — The error message in `_validate_gen_sequence_parallel` still advises users to adjust sound duration/latent FPS; because the pipeline now pads sound latents automatically, this error is unreachable through the normal path and the guidance is confusing if it fires (e.g., from direct transformer misuse). Please reword the message to state that the pipeline pads automatically and this check only applies when the transformer is called without pipeline‑level padding.

tests/diffusion/models/cosmos3/test_cosmos3_pipeline.py:1468 [normal] — The test lambda `lambda *args, **kwargs: (sound_latents, 4)` now silently accepts the new `sp_video_shape` keyword, so the pipeline‑level integration of the padding path when sequence parallelism is active is not exercised. Add a test that mocks `get_ulysses_parallel_world_size` to 2, passes a non‑None `sp_video_shape`, and asserts that `_prepare_sound_latents` returns the padded latent frame count to prevent regressions.

tests/diffusion/models/cosmos3/test_cosmos3_pipeline.py:864 [unverified] — The `StubCosmos3Transformer` used in `test_prepare_latents_for_video_image_sound_and_action` lacks the new `sound_latent_frames_for_sequence_parallel` method. The test currently passes only because it does not exercise the padding path, but a future test that passes a non‑None `sp_video_shape` would crash with an `AttributeError`. Verify whether any CI configuration exercises this stub with the new parameter, and if not, consider either adding the method to the stub or documenting the fragility.

transformer_cosmos3.py:1398-1400 [unverified] — The pad expression `pad = (-(base + sound_frames)) % ulysses_size` is correct but dense. Please add an inline comment (e.g., `# smallest non‑negative k such that (base+sound_frames+k) % ulysses_size == 0`) to improve readability.

transformer_cosmos3.py:1390-1395 [nit] — The method comment does not clarify that `video_shape` expects latent‑space dimensions (T_latent, H_latent, W_latent). Add a one‑line note stating that the tuple must be in latent space to prevent callers from passing pixel dimensions and causing patch‑size mismatches.

pipeline_cosmos3.py:1666-1686 [nit] — The `sp_num_vision_items` parameter in `_prepare_sound_latents` is never passed by any pipeline caller and defaults to 1. Because sound is already rejected when transfer/control is present, the parameter is dead code. Either remove it to keep the interface lean, or add a comment documenting it as future‑proofing and create a test that exercises a value >1.

REQUEST CHANGES
```