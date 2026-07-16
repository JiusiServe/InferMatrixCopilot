# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

This is **not a bug** — it's a run-level mismatch.

## Root cause

Your test command omits `--run-level`, which defaults to `core_model` ([`tests/helpers/fixtures/run_args.py:8`](https://github.com/vllm-project/vllm-omni/blob/main/tests/helpers/fixtures/run_args.py#L8)). Under `core_model`, [`_add_dummy_load_format()` in `tests/helpers/stage_config.py:670-682`](https://github.com/vllm-project/vllm-omni/blob/main/tests/helpers/stage_config.py#L670-L682) patches **every stage** in the deploy config to `load_format: dummy`. With dummy (random) weights, all three stages output nonsense:

- **Thinker stage** (text output): `Joe Joe Joe ...`
- **Code2wav stage** (audio output): Welsh-like gibberish (`Yn ymwneud yw'r llwyddiad...`)

This behavior was extended to online serving by [PR #4354](https://github.com/vllm-project/vllm-omni/pull/4354).

The test file itself declares `pytestmark = [pytest.mark.full_model, ...]` ([`test_qwen3_omni.py:26`](https://github.com/vllm-project/vllm-omni/blob/main/tests/examples/online_serving/test_qwen3_omni.py#L26)) — it is explicitly a full-model test that requires real weights.

## Fix

Add `--run-level=full_model`:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

## Debug (if needed)

```bash
export VLLM_LOGGING_LEVEL=DEBUG
pytest -s -v \
    tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] \
    --run-level=full_model \
    2>&1 | tee qwen3_test.log
```

With `DEBUG` logging you can confirm `stage_configs` no longer contain `load_format: dummy`.

## Verification

[@yenuo26](https://github.com/yenuo26) confirmed this passes on a local A100 with `--run-level=full_model`.

---

**Short version:** Use `--run-level=full_model` when running tests that assert real semantic output. `core_model` (the default) uses dummy weights for quick topology/smoke checks.

**Disposition:** close

## skill candidates awaiting curation

- **hunyuan-image3-base-config-guard**: Proposed guard: HunyuanImage3ForConditionalGeneration.__init__ should detect base-model tokenizer (missing <img_ratio_33..36>) and fail fast when the deploy config is the two-stage Instruct topology (
- **issue-4891-answer**: Answer draft for issue #4891 — HunyuanImage3 DiT get_cache_scale crash, duplicate of PR #4808

(promote with SkillStore.promote(name); candidates are never auto-activated)
