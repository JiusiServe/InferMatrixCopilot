# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Diagnosis

This is **not a bug** — it's a run-level misconfiguration. You ran the test without `--run-level`, which defaults to `core_model`. At that level, the test fixture **injects `load_format: dummy` into every stage's deploy config**, so all three stages (thinker, talker, code2wav) load with random/untrained weights.

**Root cause**: `tests/helpers/stage_config.py:_add_dummy_load_format()` (line 670–681)
```python
def _add_dummy_load_format(
    stage_config_path: str | None,
    run_level: str,
) -> str | None:
    """For ``core_model`` runs, patch every stage in the deploy YAML to ``load_format: dummy``."""
    if run_level != "core_model" or stage_config_path is None:
        return stage_config_path
    stage_key, load_format_path, stage_ids = _stage_load_format_paths(stage_config_path)
    return modify_stage_config(
        stage_config_path,
        updates={stage_key: {stage_id: {load_format_path: "dummy"} for stage_id in stage_ids}},
    )
```

This was extended to online-serving tests in **PR #4354** ("Reduce L2/L3 CI wall-clock time"). The `omni_server` fixture calls `stage_config_path_for_run_level()` (line 713) which dispatches here for any `core_model` run.

**What you saw**:
- Text output repeating "Joe" → the dummy thinker stage has no language understanding, so its token distribution collapses to a single repeated token.
- Audio transcribed as Welsh-like gibberish → the dummy code2wav stage produces random codec tokens; Whisper transcribes them as random phonemes.

## Fix (workaround)

Add `--run-level=full_model` to your pytest command:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

This strips `load_format: dummy` from the stage configs and loads real model weights. Confirmed passing on A100 by @yenuo26.

## Run-level reference

| Level | Weight loading | Purpose |
|---|---|---|
| `core_model` (default) | `load_format: dummy` | Fast PR-gate smoke (output format, no crash) |
| `advanced_model` | Real weights | Merge-gate accuracy/keyword checks |
| `full_model` | Real weights | Nightly/expansion full validation |

See `docs/contributing/ci/CI_5levels.md` for the full test-tier policy.

## Verification

After the fix, you should see output containing "baby" and "book" and passing similarity assertions:

```
text content is: <meaningful description of the video>
audio content is: <matching audio transcription>
similarity is: 0.9...
PASSED
```

If it still fails with `--run-level=full_model`, enable debug logging to confirm `load_format` is no longer `dummy`:

```bash
export VLLM_LOGGING_LEVEL=DEBUG
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model 2>&1 | grep load_format
```

The resolved stage configs should show **no** `load_format: dummy` entries.


**Disposition:** close
