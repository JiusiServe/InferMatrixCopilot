# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root cause

This is **not a bug** — it's a test run-level mismatch. You ran:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0]
```

without specifying `--run-level`. The pytest fixture defaults to `--run-level=core_model`:

- **`tests/helpers/fixtures/run_args.py:7`** — `default="core_model"`

In `core_model` mode, `_add_dummy_load_format` (`tests/helpers/stage_config.py:672-681`) patches **every stage** in the deploy YAML to `load_format: dummy`. This means all three stages (thinker, talker, code2wav) load with random dummy weights instead of real model weights, producing the repeated "Joe" output you saw.

This behavior was extended to online serving tests in **PR #4354** to reduce CI wall-clock time — `core_model` tests only verify plumbing (server startup, request routing), not output quality.

## Fix

Add `--run-level=full_model` to load real weights:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

For debugging, enable verbose engine logging:

```bash
export VLLM_LOGGING_LEVEL=DEBUG
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model 2>&1 | tee qwen3_test.log
```

## Verification

akshatvishu confirmed the dummy-weight mechanism with DEBUG logs showing `'load_format': 'dummy'` on all three stages. yenuo26 independently verified the test passes with `--run-level=full_model` on an A100.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
