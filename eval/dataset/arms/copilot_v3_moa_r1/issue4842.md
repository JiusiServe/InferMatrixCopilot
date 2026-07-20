# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
Test run without `--run-level=full_model`; the default `--run-level=core_model` triggers `_add_dummy_load_format()` in `tests/helpers/stage_config.py:731-736`, which patches `load_format: dummy` into every stage’s config (`tests/helpers/stage_config.py:713`). The dummy weights produce gibberish (repeated "Joe" and Welsh speech) that fails the semantic assertions.

### Fix
Append `--run-level=full_model` to the pytest invocation: `pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model`.

### Preconditions
Real Qwen/Qwen3-Omni-30B-A3B-Instruct weights locally available; ≥2 GPUs of class H100/MI325; `--run-level=full_model` must be explicitly passed.

### Verification
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model  (passing confirmed on A100 by @yenuo26).

### Prevention
Add a runtime assertion in the `omni_server` fixture: if a test is marked `full_model` and contains semantic assertions (e.g., keywords, similarity) but `run_level == 'core_model'`, fail immediately with a message explaining that `--run-level=full_model` is required.

### Disposition
close

### Additional context
## Not a bug — missing `--run-level=full_model`

This test failure is **not a defect in vLLM-Omni**. It occurs because the test was run with the default `--run-level=core_model`, which intentionally patches all pipeline stages to use `load_format: dummy` (random weights). Dummy weights produce nonsensical output—the repeated “Joe” tokens and the incoherent Welsh audio seen in the logs are exactly what is expected when real model inference is skipped.

### Root cause

The test `test_send_multimodal_request_002` is explicitly marked as an **L4 full‑model test**:
```python
# tests/examples/online_serving/test_qwen3_omni.py:26
pytestmark = [pytest.mark.full_model, pytest.mark.example, pytest.mark.omni]
```

However, the pytest `--run-level` option defaults to `core_model` (see `tests/helpers/fixtures/run_args.py:5-9`). When `run_level == "core_model"`, the helper `stage_config_path_for_run_level()` (in `tests/helpers/stage_config.py:713`) calls `_add_dummy_load_format()`, which inserts `'load_format': 'dummy'` into every stage’s engine configuration. The attached debug log confirms that all three stages (thinker, talker, code2wav) were loaded with dummy weights, causing the model to generate garbage that fails the keyword and semantic similarity assertions.

### Fix

Run the test with `--run-level=full_model` to load the actual model weights:
```bash
pytest -s -v \
  tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] \
  --run-level=full_model
```

For verbose debugging (optional):
```bash
export VLLM_LOGGING_LEVEL=DEBUG
pytest -s -v \
  tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] \
  --run-level=full_model \
  2>&1 | tee qwen3_test.log
```

### Additional note

The issue body shows a `--video-path` argument that **does not exist** in the upstream test. The repository version uses `--query-type use_video`, which handles video path resolution internally. Please make sure you are running the unmodified test file from the official repository.

### Requirements

- **Hardware**: H100 or MI325, minimum 2 GPUs (per `@hardware_test`).
- **Model weights**: Real `Qwen/Qwen3-Omni-30B-A3B-Instruct` weights must be accessible locally (no network download at test time).

### Verification

@yenuo26 confirmed this test passes on A100 with the correct run-level. The exact command:
```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

You can also verify that real weights are being loaded by checking the stage config dump; with `--run-level=full_model`, `'load_format'` will not be `'dummy'`.

### Prevention

To avoid this confusion for future users, consider adding a runtime guard in the `omni_server` fixture (or `iter_omni_server`) that fails immediately with a clear error message when a `@pytest.mark.full_model` test that contains semantic assertions is executed at `core_model` run-level, rather than allowing the test to produce misleading dummy‑weight output.

### Closing note

This issue was closed as **invalid** — no code change is needed. Reopen only if the test still fails with `--run-level=full_model` and real weights on compatible hardware.
