# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Diagnosis: run-level misconfiguration (not a bug)

This is **not a model regression or hallucination bug** — it's a `--run-level` misconfiguration. The test `test_send_multimodal_request_002` produces semantic assertions (`"baby"`, `"book"` in the video caption), which requires **real model weights**. You ran with the default `--run-level=core_model`, which loads **dummy (random) weights** in every stage.

### Root cause

1. **`tests/helpers/fixtures/run_args.py:8`** — the `--run-level` pytest option defaults to `"core_model"`:
   ```python
   parser.addoption("--run-level", action="store", default="core_model", ...)
   ```

2. **`tests/helpers/stage_config.py:702-707`** (`_add_dummy_load_format`) — when `run_level == "core_model"`, every stage in the deploy YAML is patched to `load_format: dummy`:
   ```python
   def _add_dummy_load_format(stage_config_path, run_level):
       if run_level != "core_model" or stage_config_path is None:
           return stage_config_path
       # patches all stages with load_format: dummy
   ```

3. **`tests/helpers/stage_config.py:713-718`** (`stage_config_path_for_run_level`) — routes `core_model` → dummy injection, `advanced_model`/`full_model` → strips dummy so real weights load.

This behavior was extended to online serving in **PR #4354**.

### Why the output looks like that

- **Text**: "Joe" repeated — a single token stuck in a loop. This is the **classic signature of dummy weights**: the model has random parameters and produces degenerate token sequences.
- **Audio**: Welsh-like gibberish (`Yn ymwneud yw'r llwyddiad...`) — the code2wav stage also has dummy weights, producing nonsensical audio tokens that ASR transcribes as random Welsh.

This is exactly what `core_model` is designed for: **plumbing validation only** (does the pipeline connect? do stages launch? does the request round-trip?), not semantic correctness.

### Fix

Add `--run-level=full_model` to your pytest command:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

### Workaround (if you don't have real weights)

If you don't have the Qwen3-Omni-30B-A3B-Instruct weights downloaded, the test cannot pass — `full_model` requires the real checkpoint. For CI plumbing checks, use `core_model` with no semantic assertions.

### Verification

This exact command passes on A100 (verified by @yenuo26 on 2026-07-03):
```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

### Thread grounding

- **@akshatvishu** (2026-07-02): identified the root cause, linked PR #4354, provided the exact fix command, and showed DEBUG logs confirming all 3 stages loaded with `load_format: 'dummy'`.
- **@yenuo26** (2026-07-03): verified the test passes on A100 with `--run-level=full_model` and closed the issue as "invalid".

### Triage verdict: `invalid` (not a bug)

The observable behavior is **expected** when running a `full_model`-marked test with `--run-level=core_model`. The issue is already closed. Evidence that would reopen: the same test failing with `--run-level=full_model` on A100/H100 with real weights loaded.

### Note on test code differences

Your test code includes `--video-path` and `--prompt` arguments not present in the current repo's `test_qwen3_omni.py`. This is acceptable — the client script accepts those args — but the current repo version of the test omits them and relies on defaults in the client script. This difference does not affect the run-level issue.

## draft_answer

## Diagnosis: run-level misconfiguration (not a bug)

This is **not a model regression or hallucination bug** — it's a `--run-level` misconfiguration. The test `test_send_multimodal_request_002` produces semantic assertions (`"baby"`, `"book"` in the video caption), which requires **real model weights**. You ran with the default `--run-level=core_model`, which loads **dummy (random) weights** in every stage.

### Root cause

1. **`tests/helpers/fixtures/run_args.py:8`** — the `--run-level` pytest option defaults to `"core_model"`:
   ```python
   parser.addoption("--run-level", action="store", default="core_model", ...)
   ```

2. **`tests/helpers/stage_config.py:702-707`** (`_add_dummy_load_format`) — when `run_level == "core_model"`, every stage in the deploy YAML is patched to `load_format: dummy`:
   ```python
   def _add_dummy_load_format(stage_config_path, run_level):
       if run_level != "core_model" or stage_config_path is None:
           return stage_config_path
       # patches all stages with load_format: dummy
   ```

3. **`tests/helpers/stage_config.py:713-718`** (`stage_config_path_for_run_level`) — routes `core_model` → dummy injection, `advanced_model`/`full_model` → strips dummy so real weights load.

This behavior was extended to online serving in **PR #4354**.

### Why the output looks like that

- **Text**: "Joe" repeated — a single token stuck in a loop. This is the **classic signature of dummy weights**: the model has random parameters and produces degenerate token sequences.
- **Audio**: Welsh-like gibberish (`Yn ymwneud yw'r llwyddiad...`) — the code2wav stage also has dummy weights, producing nonsensical audio tokens that ASR transcribes as random Welsh.

This is exactly what `core_model` is designed for: **plumbing validation only** (does the pipeline connect? do stages launch? does the request round-trip?), not semantic correctness.

### Fix

Add `--run-level=full_model` to your pytest command:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

### Workaround (if you don't have real weights)

If you don't have the Qwen3-Omni-30B-A3B-Instruct weights downloaded, the test cannot pass — `full_model` requires the real checkpoint. For CI plumbing checks, use `core_model` with no semantic assertions.

### Verification

This exact command passes on A100 (verified by @yenuo26 on 2026-07-03):
```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

### Thread grounding

- **@akshatvishu** (2026-07-02): identified the root cause, linked PR #4354, provided the exact fix command, and showed DEBUG logs confirming all 3 stages loaded with `load_format: 'dummy'`.
- **@yenuo26** (2026-07-03): verified the test passes on A100 with `--run-level=full_model` and closed the issue as "invalid".

### Triage verdict: `invalid` (not a bug)

The observable behavior is **expected** when running a `full_model`-marked test with `--run-level=core_model`. The issue is already closed. Evidence that would reopen: the same test failing with `--run-level=full_model` on A100/H100 with real weights loaded.

### Note on test code differences

Your test code includes `--video-path` and `--prompt` arguments not present in the current repo's `test_qwen3_omni.py`. This is acceptable — the client script accepts those args — but the current repo version of the test omits them and relies on defaults in the client script. This difference does not affect the run-level issue.

---

## Step diagnostics

### fetch

### draft
- **status**: success
- **summary**: This is not a bug but a run-level misconfiguration. The test `test_send_multimodal_request_002` requires real model weights (`--run-level=full_model`), but the reporter ran with the default `--run-level=core_model`, which injects `load_format: dummy` into every stage's config — producing the observed garbage output (repeated token 'Joe' for text, nonsensical Welsh-like audio from the code2wav stage). The issue was already diagnosed by @akshatvishu and closed as 'invalid' by @yenuo26 after verifying the test passes on A100 with the correct run-level.
- **findings**: ["Root cause: `tests/helpers/fixtures/run_args.py:8` — the `--run-level` pytest option defaults to `'core_model'`. The reporter did not override it.", "`tests/helpers/stage_config.py:702-707` (`_add_dummy_load_format`): when `run_level == 'core_model'`, every stage in the deploy YAML is patched with `load_format: dummy` via `modify_stage_config`.", '`tests/helpers/stage_config.py:713-718` (`stage_config_path_for_run_level`): routes `core_model` → `_add_dummy_load_format`, `advanced_model`/`full_model` → `_delete_dummy_load_format`.', 'This dummy-weight injection for online serving was extended in PR #4354 (`tests/helpers/stage_config.py`: `core_model` injects `load_format: dummy`; `advanced_model`/`full_model` strip it).', '`tests/examples/online_serving/test_qwen3_omni.py:25` — the test is marked `pytestmark = [pytest.mark.full_model, pytest.mark.example, pytest.mark.omni]`, indicating it requires real weights.', "The symptom — text output repeating a single token ('Joe') and audio output as nonsensical Welsh-like gibberish — is the classic signature of dummy (random) weights, not a model regression.", 'Fix: add `--run-level=full_model` to the pytest command. This was confirmed working on A100 by @yenuo26 (issue comment 2026-07-03).', "The reporter's test code includes `--video-path /rebase/vllm-omni/sample_demo_1.mp4` and `--prompt` args not present in the current repo version (v0.24.0rc1 vs HEAD); these are accepted but unrelated to the failure."]
- **files_read**: ['/rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2_t2/runs/issue4842/run-20260712-011123-690e06/evidence/issue_text.txt', '/rebase/vllm-omni/tests/examples/online_serving/test_qwen3_omni.py', '/rebase/vllm-omni/tests/helpers/fixtures/run_args.py', '/rebase/vllm-omni/tests/helpers/fixtures/runtime.py', '/rebase/vllm-omni/tests/helpers/runtime.py', '/rebase/vllm-omni/tests/helpers/stage_config.py']
- **files_modified**: []
- **tests_requested**: ['pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model']
- **tests_run**: []
- **assumptions**: ['The reporter has real model weights downloaded for Qwen/Qwen3-Omni-30B-A3B-Instruct (required for full_model runs).']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: No action needed — issue already diagnosed, verified, and closed as 'invalid' by maintainers. The answer draft below documents the root cause, fix, and verification for future reference.
- **answer_draft**: ## Diagnosis: run-level misconfiguration (not a bug)

This is **not a model regression or hallucination bug** — it's a `--run-level` misconfiguration. The test `test_send_multimodal_request_002` produces semantic assertions (`"baby"`, `"book"` in the video caption), which requires **real model weights**. You ran with the default `--run-level=core_model`, which loads **dummy (random) weights** in every stage.

### Root cause

1. **`tests/helpers/fixtures/run_args.py:8`** — the `--run-level` pytest option defaults to `"core_model"`:
   ```python
   parser.addoption("--run-level", action="store", default="core_model", ...)
   ```

2. **`tests/helpers/stage_config.py:702-707`** (`_add_dummy_load_format`) — when `run_level == "core_model"`, every stage in the deploy YAML is patched to `load_format: dummy`:
   ```python
   def _add_dummy_load_format(stage_config_path, run_level):
       if run_level != "core_model" or stage_config_path is None:
           return stage_config_path
       # patches all stages with load_format: dummy
   ```

3. **`tests/helpers/stage_config.py:713-718`** (`stage_config_path_for_run_level`) — routes `core_model` → dummy injection, `advanced_model`/`full_model` → strips dummy so real weights load.

This behavior was extended to online serving in **PR #4354**.

### Why the output looks like that

- **Text**: "Joe" repeated — a single token stuck in a loop. This is the **classic signature of dummy weights**: the model has random parameters and produces degenerate token sequences.
- **Audio**: Welsh-like gibberish (`Yn ymwneud yw'r llwyddiad...`) — the code2wav stage also has dummy weights, producing nonsensical audio tokens that ASR transcribes as random Welsh.

This is exactly what `core_model` is designed for: **plumbing validation only** (does the pipeline connect? do stages launch? does the request round-trip?), not semantic correctness.

### Fix

Add `--run-level=full_model` to your pytest command:

```bash
pytest -s -v tests/examples/onlin
