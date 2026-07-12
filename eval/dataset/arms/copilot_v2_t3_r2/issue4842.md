# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

> ⚠ draft shipped with caveats — agent self-assessed confidence: high; verify before relying on it.

## Root Cause

This is **not a bug** — it's a `--run-level` misconfiguration. By default, pytest uses `--run-level=core_model` (see `tests/helpers/fixtures/run_args.py:6-9`), which patches every stage's deploy config to `load_format: dummy` (`tests/helpers/stage_config.py:672-677`). All three pipeline stages — **thinker**, **talker**, and **code2wav** — load with random dummy weights, producing the repetitive "Joe" / Welsh gibberish output you saw.

The test `test_send_multimodal_request_002` asserts real semantic keywords (`baby`, `book`), which dummy weights can never satisfy.

## Fix

Run the test with `--run-level=full_model` to load real model weights:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

The `full_model` (and `advanced_model`) run-levels strip the `load_format: dummy` override so real HF weights are loaded (`tests/helpers/stage_config.py:713-717`).

## Verification

Two contributors have independently verified this:
- **akshatvishu** confirmed via `VLLM_LOGGING_LEVEL=DEBUG` that all three stages load with `load_format: dummy` under the default run-level.
- **yenuo26** confirmed the test passes on an A100 with `--run-level=full_model`.

## Debugging tip

If you ever see garbage output from a manual server, check the run-level first — `--run-level=core_model` (the default) uses DUMMY weights even for online serving, as noted in the project's contributor documentation.

## draft_answer

> ⚠ draft shipped with caveats — agent self-assessed confidence: high; verify before relying on it.

## Root Cause

This is **not a bug** — it's a `--run-level` misconfiguration. By default, pytest uses `--run-level=core_model` (see `tests/helpers/fixtures/run_args.py:6-9`), which patches every stage's deploy config to `load_format: dummy` (`tests/helpers/stage_config.py:672-677`). All three pipeline stages — **thinker**, **talker**, and **code2wav** — load with random dummy weights, producing the repetitive "Joe" / Welsh gibberish output you saw.

The test `test_send_multimodal_request_002` asserts real semantic keywords (`baby`, `book`), which dummy weights can never satisfy.

## Fix

Run the test with `--run-level=full_model` to load real model weights:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

The `full_model` (and `advanced_model`) run-levels strip the `load_format: dummy` override so real HF weights are loaded (`tests/helpers/stage_config.py:713-717`).

## Verification

Two contributors have independently verified this:
- **akshatvishu** confirmed via `VLLM_LOGGING_LEVEL=DEBUG` that all three stages load with `load_format: dummy` under the default run-level.
- **yenuo26** confirmed the test passes on an A100 with `--run-level=full_model`.

## Debugging tip

If you ever see garbage output from a manual server, check the run-level first — `--run-level=core_model` (the default) uses DUMMY weights even for online serving, as noted in the project's contributor documentation.

---

## Step diagnostics

### fetch

### draft
- **status**: needs_review
- **summary**: Issue #4842 is a run-level misconfiguration, not a bug. The test was run with the default `--run-level=core_model`, which patches all stage configs to `load_format: dummy` (random weights) — producing the repetitive "Joe" output instead of real semantic content. Two collaborators already confirmed the diagnosis and the issue is closed as invalid.
- **findings**: ["Root cause: `--run-level` defaults to `core_model` (tests/helpers/fixtures/run_args.py:6-9), which triggers `_add_dummy_load_format` (tests/helpers/stage_config.py:672-677) to inject `load_format: dummy` into every stage's engine_args — all three pipeline stages (thinker, talker, code2wav) load random weights.", 'The test `test_send_multimodal_request_002` asserts real semantic keywords (`baby`, `book`) which dummy weights can never satisfy. This test requires real model weights.', 'Fix: pass `--run-level=full_model` (or `advanced_model`) on the pytest command line to strip the dummy load_format and load real weights (tests/helpers/stage_config.py:713-717).', 'Two contributors (akshatvishu, yenuo26) independently verified: akshatvishu showed the DEBUG log proving all three stages load `load_format: dummy`; yenuo26 confirmed the test passes with `--run-level=full_model` on an A100.', "The repo briefing explicitly warns: '--run-level defaults to core_model = DUMMY weights even in online serving; garbage output on a manual server is run-level misconfig — use --run-level=full_model for behavior tests.'"]
- **files_read**: ['/rebase/vllm-omni/tests/examples/online_serving/test_qwen3_omni.py', '/rebase/vllm-omni/tests/helpers/fixtures/run_args.py', '/rebase/vllm-omni/tests/helpers/stage_config.py', '/rebase/vllm-omni/tests/helpers/fixtures/runtime.py', '/rebase/vllm-omni/tests/helpers/runtime.py']
- **files_modified**: []
- **tests_requested**: ['pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model']
- **tests_run**: []
- **assumptions**: ['The user is running on hardware meeting the test requirements (H100/A100 or MI325 with 2 GPUs) since the server started and responded — just with dummy weights.', "The issue's label 'invalid' and closure by yenuo26 reflect that the maintainers consider this a usage/config issue, not a code bug."]
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: If the answer is posted, the issue is already resolved/closed. No further action needed unless the user still encounters problems after switching to `--run-level=full_model`.
- **answer_draft**: ## Root Cause

This is **not a bug** — it's a `--run-level` misconfiguration. By default, pytest uses `--run-level=core_model` (see `tests/helpers/fixtures/run_args.py:6-9`), which patches every stage's deploy config to `load_format: dummy` (`tests/helpers/stage_config.py:672-677`). All three pipeline stages — **thinker**, **talker**, and **code2wav** — load with random dummy weights, producing the repetitive "Joe" / Welsh gibberish output you saw.

The test `test_send_multimodal_request_002` asserts real semantic keywords (`baby`, `book`), which dummy weights can never satisfy.

## Fix

Run the test with `--run-level=full_model` to load real model weights:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

The `full_model` (and `advanced_model`) run-levels strip the `load_format: dummy` override so real HF weights are loaded (`tests/helpers/stage_config.py:713-717`).

## Verification

Two contributors have independently verified this:
- **akshatvishu** confirmed via `VLLM_LOGGING_LEVEL=DEBUG` that all three stages load with `load_format: dummy` under the default run-level.
- **yenuo26** confirmed the test passes on an A100 with `--run-level=full_model`.

## Debugging tip

If you ever see garbage output from a manual server, check the run-level first — `--run-level=core_model` (the default) uses DUMMY weights even for online serving, as noted in the project's contributor documentation.
