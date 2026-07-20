# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
tests/helpers/stage_config.py:_add_dummy_load_format (line ~708) — when `run_level == 'core_model'` (the pytest default from `tests/helpers/fixtures/run_args.py:9`), every stage in the deploy YAML gets `load_format: dummy` injected. The model then produces random/uninitialized-weight output instead of semantic content. This test asserts real semantic keywords (`baby`, `book`) and is marked `pytest.mark.full_model`; running it under `core_model` with dummy weights is a configuration mismatch, not a code defect.

### Fix
Run the test with `--run-level=full_model`:
```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

### Preconditions
Real Qwen3-Omni-30B-A3B-Instruct checkpoint weights must be accessible (local HF cache in offline mode). Requires 2× GPU (H100/A100/MI325 per the `@hardware_test` decorator). The `--video-path` must point to a valid video file (the reported custom path `/rebase/vllm-omni/sample_demo_1.mp4` should work if the file exists).

### Verification
With `--run-level=full_model`, the expanded stage configs (visible at DEBUG log level) no longer contain `'load_format': 'dummy'`. The text output contains the keywords `baby` and `book`, and the text-audio cosine similarity exceeds 0.8.

### Prevention
The test is already correctly marked `pytest.mark.full_model`. CI (merge/weekly) already uses the correct run-level. For local development, consider a conftest hook that warns or errors when a test marked `full_model` is invoked without `--run-level=full_model` or `--run-level=advanced_model`.

### Disposition
keep-open

### Additional context
## Root Cause

This is **not a bug** — it's expected behavior from a `run-level` mismatch.

The default pytest `--run-level` is `core_model` (`tests/helpers/fixtures/run_args.py:9`). Since PR #4354, `core_model` patches every stage in the deploy YAML to `load_format: dummy` (see `_add_dummy_load_format` in `tests/helpers/stage_config.py:~708`). All three stages — thinker, talker, and code2wav — load with **uninitialized/random weights**. With dummy weights the model outputs repetitive nonsense: "Joe" repeated 75 times for text, and Welsh-like gibberish for audio.

The test you ran (`test_send_multimodal_request_002`) asserts real semantic content: it checks that the output contains `"baby"` and `"book"` and that text-audio cosine similarity exceeds 0.8. This is only possible with real model weights. The test file declares `pytestmark = [pytest.mark.full_model, ...]` (line 25) — it is explicitly intended for `full_model` runs.

## Fix

This strips the `load_format: dummy` override (via `_delete_dummy_load_format` in `stage_config.py:~721`) and loads real weights.

If you want to debug the config being used:
```bash
export VLLM_LOGGING_LEVEL=DEBUG
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model 2>&1 | tee qwen3_test.log
```

## Verification

Collaborator @yenuo26 verified this passes on an A100 with `--run-level=full_model`. The `load_format` fields in the expanded stage configs will no longer show `dummy`.

## Prevention

This is a common footgun. The test is already correctly marked `pytest.mark.full_model`, so CI (`test-merge.yml` / weekly) runs it with `--run-level=full_model`. For local runs, the `--run-level` default of `core_model` is documented in the [CI five-level docs](docs/contributing/ci/CI_5levels.md). Consider adding a `conftest.py` or pytest hook that warns when a `full_model`-marked test is invoked without `--run-level=full_model`.

## Related

- PR #4354: Extended `load_format: dummy` injection from offline/runner paths to online-serving fixtures
- Test file: `tests/examples/online_serving/test_qwen3_omni.py` (pytestmark includes `full_model`)
- Fixture plumbing: `tests/helpers/stage_config.py::_add_dummy_load_format` / `stage_config_path_for_run_level`
