# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Diagnosis: not a bug — run-level misconfiguration

Your test ran with the default `--run-level=core_model`, which loads **dummy (random) weights** into all model stages. The output you see — repeated "Joe" for text and Welsh-sounding gibberish for audio — is exactly what dummy weights produce.

### Root cause

`tests/helpers/stage_config.py::_add_dummy_load_format` (lines 668–681) patches every stage in the deploy YAML to `load_format: dummy` when `run_level == "core_model"`:

```python
def _add_dummy_load_format(stage_config_path, run_level):
    """For ``core_model`` runs, patch every stage in the deploy YAML to ``load_format: dummy``."""
    if run_level != "core_model" or stage_config_path is None:
        return stage_config_path
    stage_key, load_format_path, stage_ids = _stage_load_format_paths(stage_config_path)
    return modify_stage_config(
        stage_config_path,
        updates={stage_key: {stage_id: {load_format_path: "dummy"} for stage_id in stage_ids}},
    )
```

The `--run-level` default is `core_model` (`tests/helpers/fixtures/run_args.py` line 9). This behavior was extended to online serving in PR #4354 — before that PR, `core_model` didn't always inject `load_format: dummy` for online serving tests.

The test itself is marked `pytest.mark.full_model` (line 24 of `tests/examples/online_serving/test_qwen3_omni.py`), indicating it requires real weights for meaningful output.

### Fix / workaround

Run with `--run-level=full_model` to load real weights:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

If you need debug output:

```bash
export VLLM_LOGGING_LEVEL=DEBUG
pytest -s -v \
    tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] \
    --run-level=full_model \
    2>&1 | tee qwen3_test.log
```

### Verification

@yenuo26 already verified this passes on A100 with `--run-level=full_model`. You can confirm by checking that the DEBUG log shows `load_format` is **not** `"dummy"` (it should be absent or set to `"auto"`), and the text output should contain meaningful content like "baby" and "book".

### Note on A100 vs H100

The test is marked `@hardware_test(res={"cuda": "H100", "rocm": "MI325"}, num_cards=2)`, targeting H100/MI325. On A100 you may need to adjust per-stage `gpu_memory_utilization` in the deploy config if you hit OOM, since the 3-stage Qwen3-Omni pipeline is VRAM-heavy. @akshatvishu demonstrated running all 3 stages on a single MI300x by lowering memory utilization.

**Disposition:** close
