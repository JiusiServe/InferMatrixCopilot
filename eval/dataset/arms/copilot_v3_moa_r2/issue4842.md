# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
The test was invoked with the default --run-level=core_model, which patches all stage configs to load_format: dummy (random weights) via tests/helpers/stage_config.py:713-718. With random weights, the model produces hallucinated output (repeated 'Joe' tokens) instead of meaningful video descriptions containing 'baby' and 'book'.

### Fix
Re-run the test with --run-level=full_model to load real model weights: pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model

### Preconditions
2× GPU with sufficient VRAM for Qwen/Qwen3-Omni-30B-A3B-Instruct (the test requires H100 or MI325), real model weights accessible via HuggingFace cache or local snapshot, and the sample video file sample_demo_1.mp4 present at the expected path.

### Verification
The collaborator @yenuo26 verified the test passes on A100 with --run-level=full_model. Reproduce with: pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model

### Prevention
Tests marked pytest.mark.full_model should be skipped or emit a warning when --run-level=core_model is active, so users get a clear message instead of mysterious assertion failures. Alternatively, the test fixture could check the run level and skip with a descriptive message.

### Disposition
close

### Additional context
## This is a run-level mismatch, not a bug

The test `test_send_multimodal_request_002` asserts **real semantic output** — it checks that the model describes the video with keywords "baby" and "book", and that the audio output matches the text. To produce meaningful output, the model needs real weights.

The test module is explicitly marked `pytest.mark.full_model` ([`tests/examples/online_serving/test_qwen3_omni.py:17`](tests/examples/online_serving/test_qwen3_omni.py#L17)), which means it must be run with real model weights.

However, the default `--run-level=core_model` patches every stage's config to `load_format: dummy` ([`tests/helpers/stage_config.py:713-718`](tests/helpers/stage_config.py#L713-L718)), which loads **random weights** instead of real ones. With random weights, the model produces degenerate output — repeating a single token ("Joe") for text and nonsensical Welsh audio — which is exactly what the logs show.

### Fix

Run the test with `--run-level=full_model` so real weights are loaded:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

This was verified locally on A100 by @yenuo26 and the test passes.

### Why core_model produces garbage

The `stage_config_path_for_run_level()` function ([`tests/helpers/stage_config.py:713-718`](tests/helpers/stage_config.py#L713-L718)) applies `load_format: dummy` to all stages when `run_level == 'core_model'`. The `DummyModelLoader` skips `load_weights()` entirely and randomizes parameters in place, so every inference call produces random tokens. The repeated "Joe" pattern is the repetition penalty (1.05 on stage 1) fighting against the degenerate distribution — it keeps resampling the same token.

### Rule of thumb

- Tests marked `pytest.mark.core_model` → can run with `--run-level=core_model` (dummy weights OK for plumbing tests)
- Tests marked `pytest.mark.full_model` → **must** run with `--run-level=full_model` (real weights required for semantic assertions)

If you want to run all tests in the examples directory, use `--run-level=full_model` and ensure you have enough GPU memory for `Qwen/Qwen3-Omni-30B-A3B-Instruct` with 2 GPUs.
