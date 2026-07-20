# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
The default `--run-level=core_model` causes `tests/helpers/stage_config.py::_add_dummy_load_format` (line 700–708) to patch every stage in the deploy YAML with `load_format: dummy`. The omni_server fixture in `tests/helpers/runtime.py:2832` applies this via `stage_config_path_for_run_level()`. All three stages (thinker, talker, code2wav) load dummy weights, producing deterministic gibberish output that fails the semantic keyword assertions.

### Fix
Add `--run-level=full_model` to the pytest invocation: `pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model`

### Workaround
For quick plumbing-only checks, use `--run-level=core_model` (the default) — just don't expect meaningful text/audio output. For semantic validation, always use `--run-level=full_model`.

### Preconditions
1. Real Qwen3-Omni-30B-A3B-Instruct model weights must be downloaded and accessible locally (HF offline mode). 2. Sufficient GPU VRAM: the test is marked for H100/MI325 with 2 cards; A100 with 80 GB × 2 may work with appropriate `gpu_memory_utilization` tuning. 3. The hardware gate `@hardware_test(res={'cuda': 'H100'})` may need to be bypassed for A100.

### Verification
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model

### Prevention
Consider adding a notice in the test file's docstring or in `tests/examples/online_serving/qwen3_omni/README.md` that clarifies the run-level requirement for semantic tests. The CI_5levels.md docs already document this tiering but users may miss it.

### Disposition
keep-open

### Additional context
Hi @zhumingjue138 — this is not a bug in vLLM-Omni. The output you're seeing is expected when running with the default `--run-level=core_model`, which instructs the test harness to load **dummy weights** for all three stages (thinker, talker, code2wav).

## Root cause

Since PR [#4354](https://github.com/vllm-project/vllm-omni/pull/4354), the `core_model` run-level patches the stage deploy YAML to inject `load_format: dummy` — see `tests/helpers/stage_config.py::_add_dummy_load_format`:

- `tests/helpers/stage_config.py:700–708` — for `core_model` runs, every stage gets `load_format: dummy`
- The `omni_server` fixture in `tests/helpers/runtime.py:2832` calls `stage_config_path_for_run_level(params.stage_config_path, run_level)`, which applies this patching

With dummy weights the model outputs deterministic gibberish — "Joe Joe Joe…" for text and nonsensical audio. This is by design: `core_model` is for **CI smoke tests** that only check request success and payload shape, not semantic content.

## Fix

Run the test with `--run-level=full_model` to load real weights:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

## Hardware note

The test is decorated `@hardware_test(res={'cuda': 'H100', 'rocm': 'MI325'}, num_cards=2)`. On an A100 you may need to override the hardware gate (e.g. set the appropriate environment variable or modify the mark). Also verify your A100 has enough VRAM — the full 3-stage pipeline with real weights on Qwen3-Omni-30B-A3B-Instruct requires substantial GPU memory.

## Verification

@akshatvishu already reproduced the dummy-weight behavior and confirmed the correct invocation; @yenuo26 verified the test passes on A100 with `--run-level=full_model`.

## Prevention

This is documented in the CI levels doc. For local debugging, you can also enable debug logging:

```bash
export VLLM_LOGGING_LEVEL=DEBUG
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model 2>&1 | tee qwen3_test.log
```

The debug log will show each stage's `load_format` — if it says `'load_format': 'dummy'`, you're still on `core_model`.

Since this is a configuration/usage issue rather than a code defect, the issue was closed as `invalid`. Feel free to re-test with the corrected command.
