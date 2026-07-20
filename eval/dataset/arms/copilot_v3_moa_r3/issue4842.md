# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
Default CLI `--run-level=core_model` in `tests/helpers/fixtures/run_args.py:12` triggers `_add_dummy_load_format()` at `tests/helpers/stage_config.py:670-682`, forcing `load_format: 'dummy'` for all three Qwen3‑Omni stages (thinker, talker, code2wav) because `core_model` is not `advanced_model` nor `full_model`. The dummy (random) weights produce non‑semantic output, failing the `baby`/`book` assertions.

### Fix
Run the test with `--run-level=full_model`:
```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

### Preconditions
Real Qwen3-Omni-30B-A3B-Instruct weights accessible locally (via HuggingFace cache or snapshot). At least 2 GPUs with sufficient memory (A100 or H100 per `@hardware_test` decorator). vLLM‑Omni version that includes PR #4354 or later.

### Verification
Run the corrected command; the test should exit with code 0, the text output must contain 'baby' and 'book', and the audio‑text cosine similarity must be >0.8. This was confirmed by @yenuo26 on an A100 environment.

### Prevention
Add a conftest guard (or a fixture check) that detects `@pytest.mark.full_model` on a test and verifies the active `--run-level` is `full_model`. If not, it should `pytest.fail` (or `pytest.skip`) with a clear diagnostic. Optionally, log a warning in the `omni_server` fixture when insufficient run level is used for a full‑model‑marked test.

### Disposition
close — closed as 'invalid' by collaborator @yenuo26 after confirming the test passes with `--run-level=full_model` on A100. Reopen only if the failure recurs with `--run-level=full_model` on equivalent hardware.

### Additional context
# Not a model hallucination — default test run level loads dummy weights

This failure occurs because the test was executed **without specifying `--run-level`**, which defaults to `core_model` in `tests/helpers/fixtures/run_args.py` (line 12).

When `run_level == "core_model"` (or any level not `"advanced_model"` or `"full_model"`), the test infrastructure patches **every stage** in the deploy YAML to use `load_format: "dummy"` via `tests/helpers/stage_config.py:670-682` (`_add_dummy_load_format`). This dummy‑weight behaviour was extended to online serving configurations by **PR #4354**.

With random (dummy) weights loaded, all three Qwen3‑Omni stages — thinker (LLM), talker (LLM), and code2wav (audio) — produce garbage output:
- **Text stage**: repeated single tokens `"Joe"` instead of a meaningful description of the video.
- **Audio stage**: random audio that speech‑to‑text transcribes as nonsensical Welsh.

This is expected behaviour of a model running with random weights, not a model hallucination bug.

## Fix

Run the test with `--run-level=full_model` so that real model weights are loaded:

```bash
pytest -s -v \
  tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] \
  --run-level=full_model
```

For debugging with verbose logs:

```bash
export VLLM_LOGGING_LEVEL=DEBUG
pytest -s -v \
  tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] \
  --run-level=full_model \
  2>&1 | tee qwen3_test.log
```

You should see all three stage configs loading with `load_format` absent (real weights) instead of `"dummy"`.

## Verification

- Collaborator @yenuo26 confirmed the test passes with the above command on an A100 environment.
- The test asserts that the text output contains `"baby"` and `"book"` and that the audio‑text cosine similarity is >0.8; both will succeed.

## Prevention

The test file is already marked with `pytestmark = [pytest.mark.full_model, ...]`, indicating that real weights are required. However, the `@hardware_test` decorator only enforces GPU type/count — it does **not** automatically set the run level.

A guard should be added so that a test carrying the `@pytest.mark.full_model` marker **fails or skips** when `--run-level` is not `"full_model"`, with a clear error message. For example, in a `conftest.py`:
```python
@pytest.fixture(autouse=True)
def _check_run_level_for_full_model_tests(request):
    if request.node.get_closest_marker("full_model"):
        run_level = request.config.getoption("--run-level", default="core_model")
        if run_level != "full_model":
            pytest.fail(
                f"Test requires --run-level=full_model but got {run_level}. "
                "Please run with --run-level=full_model."
            )
```
This prevents the same footgun for future contributors.

## Disposition

**Closed as invalid** by @yenuo26. Reopen only if the failure persists **with `--run-level=full_model`** on equivalent hardware (A100‑2x, H100‑2x, MI325‑2x).
