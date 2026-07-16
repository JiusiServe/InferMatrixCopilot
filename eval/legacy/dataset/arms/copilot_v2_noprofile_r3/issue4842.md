# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Diagnosis

This is **not a bug** — you ran the test without setting the correct run level.

The default `--run-level=core_model` (see `tests/helpers/fixtures/run_args.py`) causes the test framework to inject `load_format: dummy` into **every** stage's engine config. This was extended to online serving tests in **PR #4354**.

With dummy weights all three stages (thinker, talker, code2wav) produce garbage: your "Joe Joe Joe…" text output and Welsh-sounding audio are exactly what you'd expect from uninitialized weights.

### Root cause (code trace)

1. `--run-level` defaults to `"core_model"` — `tests/helpers/fixtures/run_args.py` line `default="core_model"`
2. `stage_config_path_for_run_level()` dispatches to `_add_dummy_load_format()` — `tests/helpers/stage_config.py:713`
3. `_add_dummy_load_format()` patches every stage with `load_format: dummy` — same file, line ~680
4. `iter_omni_server()` calls this before launching the server — `tests/helpers/runtime.py:2832`

### Fix

Add `--run-level=full_model` to your pytest command:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

For debugging, enable debug logging:

```bash
export VLLM_LOGGING_LEVEL=DEBUG
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model 2>&1 | tee qwen3_test.log
```

In the debug output you should see `load_format` is **not** `dummy` for any stage.

### Verification

Run the command above with `--run-level=full_model`. The test should pass — collaborator @yenuo26 confirmed this on their A100.

### Related

- PR #4354: extended `load_format: dummy` injection to online serving fixtures
- The `pytest.mark.full_model` marker on the test file is for CI job filtering, not for controlling `--run-level` — they are separate mechanisms.

**Verdict:** invalid (user misconfiguration). Reopen only if the failure reproduces with `--run-level=full_model`.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
