# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': True, 'post': False, 'params': {}}

## draft_answer

## Diagnosis

This is **not a model bug** — the test was run at the default `--run-level=core_model`, which loads **dummy (random) weights** into all pipeline stages. The test asserts real semantic output (`"baby"`, `"book"`), which can only come from real weights.

### Root cause

1. **`tests/helpers/fixtures/run_args.py:9`** — the `--run-level` pytest option defaults to `"core_model"`.

2. **`tests/helpers/stage_config.py:674–680`** (`_add_dummy_load_format`) — at `core_model` level, every stage in the deploy YAML is patched with `load_format: "dummy"`, which skips real weight loading and uses uninitialized parameters.

3. **`tests/examples/online_serving/test_qwen3_omni.py:26`** — the test file is marked `pytestmark = [pytest.mark.full_model, pytest.mark.example, pytest.mark.omni]`, meaning it is gated behind `--run-level=full_model`.

### Why the output looks like it does

- **Text output (`Joe Joe Joe...`)**: The thinker stage with dummy weights produces random logits → random token IDs. The tokenizer happens to decode many of them as the subword "Joe".
- **Audio output (Welsh-like gibberish)**: The code2wav stage with dummy weights generates random audio codes → random speech-like waveforms. The ASR transcription picks up Welsh phoneme patterns because the random audio happens to sound like Welsh to whisper-small.

### Fix

Add `--run-level=full_model` to your pytest invocation:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

This was verified by @akshatvishu on MI300x and @yenuo26 on A100 — the test passes with real weights.

### Verification

Run the command above. You should see meaningful text output (containing descriptions of the video) and audio that transcribes to similar content, with cosine similarity > 0.8.

### Thread grounding

- @akshatvishu's [comment](https://github.com/vllm-project/vllm-omni/issues/4842#issuecomment-…): correctly identified `load_format: dummy` as the cause and provided the `--run-level=full_model` fix, with debug logs showing all three stages loading dummy weights.
- @yenuo26's [comment](https://github.com/vllm-project/vllm-omni/issues/4842#issuecomment-…): confirmed the test passes on A100 with the correct run-level and closed the issue as invalid.

### Disposition

**Closed as invalid.** The issue is a run-level misconfiguration, not a bug. Reopen if the test still produces garbage output when run with `--run-level=full_model`.

### Unrelated

- The NVFP4 patch log line (`NVFP4 W4A4 weight_scale NaN-clamp: installed`) is a quantization-support patch and is unrelated to this failure.
- The test's `@hardware_test(res={"cuda": "H100", "rocm": "MI325"})` targets H100/MI325, but A100 is not listed — if you're running on A100, ensure you have enough VRAM (~80 GiB across 2 GPUs for the 30B MoE model).
