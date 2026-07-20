# Run report

- task: {'kind': 'issue_answer', 'mode': 'eco', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': False, 'post': False, 'params': {}}

## draft_answer

### Root cause
tests/helpers/stage_config.py:670-683 `_add_dummy_load_format()` — when `run_level == "core_model"` (the default), every stage in the deploy YAML is patched to `load_format: dummy`, causing all three stages (thinker/talker/code2wav) to load random/mock weights instead of real model weights. The test at tests/examples/online_serving/test_qwen3_omni.py:30 is marked `pytest.mark.full_model` and asserts real semantic output.

### Fix
Run with `--run-level=full_model`:
```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

### Preconditions
Real Qwen3-Omni-30B-A3B-Instruct weights must be available locally; at least 2 GPUs (H100 or MI325).

### Verification
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model

### Prevention
Consider adding a guard in the `omni_server` fixture or `stage_config_path_for_run_level()` that emits a clear WARNING when a `pytest.mark.full_model` test is run at `core_model` level, so users immediately see why semantic assertions fail. Alternatively, add a note in `tests/examples/online_serving/qwen3_omni/README.md` about required run-level.

### Disposition
close

### Additional context
## Diagnosis: not a bug — wrong `--run-level`

Your command:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0]
```

uses the **default `--run-level=core_model`** (defined at `tests/helpers/fixtures/run_args.py:7-12`). At this level, `_add_dummy_load_format()` in `tests/helpers/stage_config.py:670-683` patches every stage in the deploy YAML to `load_format: dummy` — all three stages (thinker, talker, code2wav) load with random/mock weights, which is why you see repetitive "Joe" text and Welsh-like audio.

### Evidence

The test module declares at line 30:
```python
pytestmark = [pytest.mark.full_model, pytest.mark.example, pytest.mark.omni]
```

This test **requires real weights** (`full_model` → L4). The `core_model` (L2) run-level is designed for fast plumbing/smoke checks, not semantic correctness.

### Fix

Run with the correct run-level:

Or select by marker:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py -m full_model -k test_send_multimodal_request_002
```

### Verification

With `--run-level=full_model`, the stage configs will have `load_format: dummy` **stripped** (via `_delete_dummy_load_format()` at `tests/helpers/stage_config.py:684-707`), real weights will load, and the assertion `all(keyword in text_content for keyword in ["baby", "book"])` will pass.

### Preconditions

- Real Qwen3-Omni-30B-A3B-Instruct checkpoint available locally
- At least 2 GPUs (as required by `@hardware_test(num_cards=2)`)

### Why it looked like a bug

PR #4354 extended the `load_format: dummy` patching to online serving tests at the `core_model` level, which is why this test (which was previously passing at `core_model` without dummy weights) now produces garbage. This is intentional — `core_model` tests should not depend on real weights.

### Status

This issue was already closed as `invalid` by @yenuo26 after independent verification. @akshatvishu provided the same diagnosis with a detailed log showing all three stages loading with `load_format: dummy`.
