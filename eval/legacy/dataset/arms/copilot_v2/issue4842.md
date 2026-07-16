# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': True, 'post': False, 'params': {}}

## fetch
- **state_updates**: {'issue_text': '{"body":"### Your current environment\\n\\n<details>\\n<summary>The output of <code>python collect_env.py</code></summary>\\n\\n```text\\nYour output of `python collect_env.py` here\\n```\\n\\n</details>\\n\\n\\n### Your code version\\n\\n<details>\\n<summary>The commit id or version of vllm</summary>\\n\\n```text\\n0.24.0\\n```\\n</details>\\n<details>\\n<summary>The commit id or version of vllm-omni</summary>\\n\\n```text\\nv0.24.0rc1\\n```\\n</details>\\n\\n\\n### 🐛 Describe the bug\\n\\npytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0]\\n\\nadd local address for video\\n```\\n@hardware_test(res={\\"cuda\\": \\"H100\\", \\"rocm\\": \\"MI325\\"}, num_cards=2)\\n@pytest.mark.parametrize(\\"omni_server\\", test_params, indirect=True)\\ndef test_send_multimodal_request_002(omni_server) -> None:\\n    command = common_args + [\\n        \\"--query-type\\",\\n        \\"use_video\\",\\n        \\"--model\\",\\n        omni_server.model,\\n        \\"--video-path\\",\\n        \\"/rebase/vllm-omni/sample_demo_1.mp4\\",\\n        \\"--prompt\\",\\n        \\"What are the main activities shown in this video?\\",\\n    ]\\n    result = run_cmd(command)\\n\\n    text_content_tmp = extract_content_after_keyword(\\"Chat completion output from text:\\", result)\\n    text_content = strip_trailing_audio_saved_line(text_content_tmp)\\n\\n    # Verify text output same as audio output\\n    wav_path = extract_last_audio_saved_path(result)\\n    audio_content = convert_audio_file_to_text(output_path=f\\"./{wav_path}\\")\\n    print(f\\"text content is: {text_content}\\")\\n    print(f\\"audio content is: {audio_content}\\")\\n    assert all(keyword in text_content for keyword in [\\"baby\\", \\"book\\"]), (\\n        \\"The output does not contain any of the keywords.\\"\\n    )\\n    similarity = cosine_similarity_text(audio_content.lower(), text_content.lower())\\n    print(f\\"similarity is: {similarity}

## draft
- **status**: success
- **summary**: The reported failure is not a bug in vLLM-Omni. The test `test_send_multimodal_request_002` is marked `pytest.mark.full_model` and requires real model weights. The user ran it with the default `--run-level=core_model`, which patches all pipeline stages to use `load_format: dummy` (dummy/random weights). The garbled output (repeated "Joe" text and Welsh-like audio) is the expected behavior with dummy weights. Running with `--run-level=full_model` loads real weights and the test passes. This was confirmed by two collaborators and the issue has been closed as "invalid".
- **findings**: ['The test `test_send_multimodal_request_002` is decorated with `pytest.mark.full_model`, requiring real weights.', 'The default `--run-level` is `core_model` (see `tests/helpers/fixtures/run_args.py`), which triggers `_add_dummy_load_format` in `tests/helpers/stage_config.py` to patch all stages to `load_format: dummy`.', 'With dummy weights, the model produces random/garbled outputs — the repeated "Joe" text and Welsh-like audio are consistent with this behavior, not a model regression.', 'Collaborator `akshatvishu` identified the root cause and provided debug output showing all 3 stages loading with `load_format: dummy`.', 'Collaborator `yenuo26` verified the test passes correctly on an A100 with `--run-level=full_model`.', 'The issue is already closed with the "invalid" label.']
- **files_read**: ['/rebase/vllm-omni/tests/examples/online_serving/test_qwen3_omni.py', '/rebase/vllm-omni/tests/conftest.py', '/rebase/vllm-omni/tests/helpers/stage_config.py', '/rebase/vllm-omni/tests/helpers/fixtures/run_args.py', '/rebase/vllm-omni/tests/helpers/fixtures/config.py']
- **files_modified**: []
- **tests_requested**: ['pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model']
- **tests_run**: []
- **assumptions**: ['The issue is already resolved (closed as invalid) and only needs a clarifying answer, not a code fix.']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: No further action needed — the issue is closed. The answer draft below explains the root cause and provides the correct invocation.
- **answer_draft**: ## Root Cause: Wrong `--run-level`

The test `test_send_multimodal_request_002` is marked with `@pytest.mark.full_model`, which means it **requires real model weights** to produce meaningful text output (keywords like "baby" and "book").

You ran:
```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0]
```

This uses the **default** `--run-level=core_model`. At `core_model` level, the test framework automatically patches every pipeline stage to `load_format: dummy` (see `tests/helpers/stage_config.py` → `_add_dummy_load_format`). With dummy weights, the model has no actual knowledge and produces random/garbled tokens — which is exactly what you observed:
- Text output: repeated `"Joe"`
- Audio output: Welsh-like gibberish ("Yn ymwneud yw'r llwyddiad...")

## Fix: Use `--run-level=full_model`

Run the test with real weights:
```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

This strips the `load_format: dummy` overrides and loads the actual model weights, allowing the test to produce meaningful outputs and pass its assertions.

> **Note:** This was confirmed on A100 by a collaborator (yenuo26) — the test passes correctly with `--run-level=full_model`. The issue has been closed as "invalid" since it's a usage issue, not a code bug.

## Quick reference: Run levels

| Level | Weight Loading | Use Case |
|---|---|---|
| `core_model` (default) | `load_format: dummy` — no real weights | Fast smoke/syntax checks |
| `advanced_model` | Real weights | Integration tests |
| `full_model` | Real weights (strips dummy overrides) | Semantic/output correctness tests like this one |
- **draft_answer**: ## Root Cause: Wrong `--run-level`

The test `test_send_multimodal_request_002` is marked with `@pytest.mark.full_model`, which means it **requires real model weights** to produce meaningful text output (keywords like "baby" and "book").

You ran:
```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0]
```

This uses the **default** `--run-level=core_model`. At `core_model` level, the test framework automatically patches every pipeline stage to `load_format: dummy` (see `tests/helpers/stage_config.py` → `_add_dummy_load_format`). With dummy weights, the model has no actual knowledge and produces random/garbled tokens — which is exactly what you observed:
- Text output: repeated `"Joe"`
- Audio output: Welsh-like gibberish ("Yn ymwneud yw'r llwyddiad...")

## Fix: Use `--run-level=full_model`

Run the test with real weights:
```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

This strips the `load_format: dummy` overrides and loads the actual model weights, allowing the test to produce meaningful outputs and pass its assertions.

> **Note:** This was confirmed on A100 by a collaborator (yenuo26) — the test passes correctly with `--run-level=full_model`. The issue has been closed as "invalid" since it's a usage issue, not a code bug.

## Quick reference: Run levels

| Level | Weight Loading | Use Case |
|---|---|---|
| `core_model` (default) | `load_format: dummy` — no real weights | Fast smoke/syntax checks |
| `advanced_model` | Real weights | Integration tests |
| `full_model` | Real weights (strips dummy overrides) | Semantic/output correctness tests like this one |
- **state_updates**: {'draft_answer': '## Root Cause: Wrong `--run-level`\n\nThe test `test_send_multimodal_request_002` is marked with `@pytest.mark.full_model`, which means it **requires real model weights** to produce meaningful text output (keywords like "baby" and "book").\n\nYou ran:\n```bash\npytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0]\n```\n\nThis uses the **default** `--run-level=core_model`. At `core_model` level, the test framework automatically patches every pipeline stage to `load_format: dummy` (see `tests/helpers/stage_config.py` → `_add_dummy_load_format`). With dummy weights, the model has no actual knowledge and produces random/garbled tokens — which is exactly what you observed:\n- Text output: repeated `"Joe"`\n- Audio output: Welsh-like gibberish ("Yn ymwneud yw\'r llwyddiad...")\n\n## Fix: Use `--run-level=full_model`\n\nRun the test with real weights:\n```bash\npytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model\n```\n\nThis strips the `load_format: dummy` overrides and loads the actual model weights, allowing the test to produce meaningful outputs and pass its assertions.\n\n> **Note:** This was confirmed on A100 by a collaborator (yenuo26) — the test passes correctly with `--run-level=full_model`. The issue has been closed as "invalid" since it\'s a usage issue, not a code bug.\n\n## Quick reference: Run levels\n\n| Level | Weight Loading | Use Case |\n|---|---|---|\n| `core_model` (default) | `load_format: dummy` — no real weights | Fast smoke/syntax checks |\n| `advanced_model` | Real weights | Integration tests |\n| `full_model` | Real weights (strips dummy overrides) | Semantic/output correctness tests like this one |'}
