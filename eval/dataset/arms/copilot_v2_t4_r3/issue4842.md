# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Root Cause

This is **not a bug** — it's a run-level misconfiguration. The `--run-level` pytest flag defaults to `core_model`, which patches every pipeline stage in the deploy YAML to use `load_format: dummy` (random weights). Your test asserts real semantic output ("baby", "book" keywords), which is impossible with random weights.

**Code evidence**:
- `tests/helpers/fixtures/run_args.py:16` — `--run-level` defaults to `"core_model"`
- `tests/helpers/stage_config.py:674` — `_add_dummy_load_format()` injects `load_format: dummy` into every stage
- `tests/helpers/stage_config.py:713` — `stage_config_path_for_run_level()` applies this during server fixture setup

This behavior was extended to online serving in #4354, which is why this test that may have previously worked now produces gibberish output — all three stages (thinker, talker, code2wav) load with dummy weights as shown in your logs.

## Fix / Workaround

Use `--run-level=full_model` to load real model weights:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

For debugging, add verbose logging:

```bash
export VLLM_LOGGING_LEVEL=DEBUG
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model 2>&1 | tee qwen3_test.log
```

## Status

This issue has been verified by @yenuo26 on an A100 and closed as **invalid** — the test passes with `--run-level=full_model`.

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
