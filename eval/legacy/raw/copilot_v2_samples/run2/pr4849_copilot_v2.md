`hunyuan_image3.py:98` [nit] — The `requires_multimodal_data` parameter is accepted but never used; add a comment explaining that HunyuanImage3 always forwards multimodal data unconditionally (`# HunyuanImage3 always needs the original image for IT2I conditioning`) to match the documented intent and avoid confusion with the GLM‑Image bridge, which uses this flag.

`hunyuan_image3.py:163,179` [nit] — Log messages hardcode `Request 0` now that only one request is returned, but the static prefix is uninformative; drop the prefix or replace it with something more meaningful (e.g., include the generated text length) to make the logs actionable.

`hunyuan_image3.py:119` [nit] — `ar_output.outputs[0]` is accessed without checking for an empty `outputs` list. Add `assert ar_output.outputs, "AR output has no completions"` to document the invariant and turn a cryptic `IndexError` into a clear failure.

`orchestrator.py:1104` [unverified] — The dynamically‑dispatched `custom_process_input_func` uses `inspect.signature` to detect `sampling_params`. Verify that the GLM‑Image bridge’s `ar2diffusion` path is exercised by tests that cover this probe, so that adding `sampling_params` to the HunyuanImage3 bridge signature does not silently change the dispatch.

`tests/e2e/accuracy/test_hunyuan_image3.py` [unverified] — Confirm that `test_image_to_image_alignment_online` exists in the test suite and passes, as it was the reproduction case for the original list‑prompt batching error.

**APPROVE**