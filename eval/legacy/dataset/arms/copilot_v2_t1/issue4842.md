# Run report

- task: {'kind': 'issue_answer', 'repo': 'vllm-omni', 'pr': None, 'issue': 4842, 'report_only': True, 'post': False, 'params': {}}

## fetch
- **state_updates**: {'issue_text': '{"body":"### Your current environment\\n\\n<details>\\n<summary>The output of <code>python collect_env.py</code></summary>\\n\\n```text\\nYour output of `python collect_env.py` here\\n```\\n\\n</details>\\n\\n\\n### Your code version\\n\\n<details>\\n<summary>The commit id or version of vllm</summary>\\n\\n```text\\n0.24.0\\n```\\n</details>\\n<details>\\n<summary>The commit id or version of vllm-omni</summary>\\n\\n```text\\nv0.24.0rc1\\n```\\n</details>\\n\\n\\n### 🐛 Describe the bug\\n\\npytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0]\\n\\nadd local address for video\\n```\\n@hardware_test(res={\\"cuda\\": \\"H100\\", \\"rocm\\": \\"MI325\\"}, num_cards=2)\\n@pytest.mark.parametrize(\\"omni_server\\", test_params, indirect=True)\\ndef test_send_multimodal_request_002(omni_server) -> None:\\n    command = common_args + [\\n        \\"--query-type\\",\\n        \\"use_video\\",\\n        \\"--model\\",\\n        omni_server.model,\\n        \\"--video-path\\",\\n        \\"/rebase/vllm-omni/sample_demo_1.mp4\\",\\n        \\"--prompt\\",\\n        \\"What are the main activities shown in this video?\\",\\n    ]\\n    result = run_cmd(command)\\n\\n    text_content_tmp = extract_content_after_keyword(\\"Chat completion output from text:\\", result)\\n    text_content = strip_trailing_audio_saved_line(text_content_tmp)\\n\\n    # Verify text output same as audio output\\n    wav_path = extract_last_audio_saved_path(result)\\n    audio_content = convert_audio_file_to_text(output_path=f\\"./{wav_path}\\")\\n    print(f\\"text content is: {text_content}\\")\\n    print(f\\"audio content is: {audio_content}\\")\\n    assert all(keyword in text_content for keyword in [\\"baby\\", \\"book\\"]), (\\n        \\"The output does not contain any of the keywords.\\"\\n    )\\n    similarity = cosine_similarity_text(audio_content.lower(), text_content.lower())\\n    print(f\\"similarity is: {similarity}

## draft
- **status**: success
- **summary**: The reported failure is a run-level misconfiguration, not a model or serving bug. The test `test_send_multimodal_request_002` is marked `full_model` and requires real weights, but the reporter ran with the default `--run-level=core_model`, which patches every stage config to `load_format: dummy`. With dummy weights all three stages (thinker, talker, code2wav) produce garbage output (repeated "Joe" for text, nonsensical audio). The issue was already diagnosed by contributor akshatvishu, independently verified on A100 by collaborator yenuo26, and closed as `invalid`.
- **findings**: ["Root cause: `--run-level=core_model` (the pytest default in tests/helpers/fixtures/run_args.py:10) triggers `_add_dummy_load_format()` in tests/helpers/stage_config.py which overwrites every stage's `load_format` with `'dummy'`, causing dummy-weight garbage output.", 'The test file tests/examples/online_serving/test_qwen3_omni.py:29 declares `pytestmark = [pytest.mark.full_model, pytest.mark.example, pytest.mark.omni]`, meaning it expects real weights.', 'Contributor akshatvishu provided the debug log confirming all three stages loaded with `load_format: dummy` and suggested the `--run-level=full_model` flag.', "Collaborator yenuo26 confirmed the test passes on A100 with `--run-level=full_model` and closed the issue as 'invalid'.", 'The dummy-weight behavior for online serving was extended in PR #4354, making this a known configuration pitfall.']
- **files_read**: ['/rebase/vllm-omni-copilot/eval/dataset/arms/copilot_v2_t1/runs/issue4842/run-20260712-005220/evidence/issue_text.txt', '/rebase/vllm-omni/tests/helpers/fixtures/run_args.py', '/rebase/vllm-omni/tests/helpers/fixtures/runtime.py', '/rebase/vllm-omni/tests/helpers/runtime.py', '/rebase/vllm-omni/tests/helpers/stage_config.py', '/rebase/vllm-omni/tests/examples/online_serving/test_qwen3_omni.py', '/rebase/vllm-omni/tests/helpers/assertions.py']
- **files_modified**: []
- **tests_requested**: []
- **tests_run**: []
- **assumptions**: ["The issue reporter's A100 environment has the model weights available (needed for --run-level=full_model to work).", 'The sample_demo_1.mp4 video file was accessible at /rebase/vllm-omni/sample_demo_1.mp4 when running the test.']
- **blockers**: []
- **confidence**: high
- **failure_kind**: None
- **next_action**: The issue is already closed as 'invalid' with a clear resolution. No further action needed. The draft answer can be posted as-is.
- **answer_draft**: ## Root Cause

You're running the test with the **default `--run-level=core_model`**, which patches every stage's deploy YAML to use `load_format: dummy`. This was extended to online serving in PR #4354. With dummy weights, the thinker, talker, and code2wav stages all produce garbage — hence the repeating "Joe" text and nonsensical audio (Welsh-like gibberish).

**Mechanism** (code references):
1. `tests/helpers/fixtures/run_args.py:10` — pytest `--run-level` defaults to `"core_model"`.
2. `tests/helpers/stage_config.py:_add_dummy_load_format()` — for `core_model`, inserts `load_format: dummy` into every stage.
3. `tests/helpers/runtime.py:iter_omni_server()` calls `stage_config_path_for_run_level()` which triggers the patch.
4. All three stages (thinker, talker, code2wav) load with randomized dummy weights, producing the observed garbage.

## Fix / Workaround

Pass `--run-level=full_model` to load real weights:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

You can verify dummy vs real weights by enabling `DEBUG` logging:

```bash
export VLLM_LOGGING_LEVEL=DEBUG
pytest -s -v \
    tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] \
    2>&1 | tee qwen3_test.log
```

Look for `load_format: 'dummy'` in the stage_configs dump — that confirms core_model is active. With `--run-level=full_model` those entries will be absent and real weights will load.

## Verification

- Contributor **akshatvishu** independently reproduced the dummy-weight logging and provided the same diagnosis.
- Collaborator **yenuo26** confirmed the test passes on an A100 with `--run-level=full_model`.
- This issue has been closed as `invalid` (not a bug).

## Additional Notes

The test is marked `pytest.mark.full_model` (line 29 of `test_qwen3_omni.py`) because it asserts real semantic output (`"baby"`, `"book"` keywords, text-audio cosine similarity > 0.
- **draft_answer**: ## Root Cause

You're running the test with the **default `--run-level=core_model`**, which patches every stage's deploy YAML to use `load_format: dummy`. This was extended to online serving in PR #4354. With dummy weights, the thinker, talker, and code2wav stages all produce garbage — hence the repeating "Joe" text and nonsensical audio (Welsh-like gibberish).

**Mechanism** (code references):
1. `tests/helpers/fixtures/run_args.py:10` — pytest `--run-level` defaults to `"core_model"`.
2. `tests/helpers/stage_config.py:_add_dummy_load_format()` — for `core_model`, inserts `load_format: dummy` into every stage.
3. `tests/helpers/runtime.py:iter_omni_server()` calls `stage_config_path_for_run_level()` which triggers the patch.
4. All three stages (thinker, talker, code2wav) load with randomized dummy weights, producing the observed garbage.

## Fix / Workaround

Pass `--run-level=full_model` to load real weights:

```bash
pytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model
```

You can verify dummy vs real weights by enabling `DEBUG` logging:

```bash
export VLLM_LOGGING_LEVEL=DEBUG
pytest -s -v \
    tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] \
    2>&1 | tee qwen3_test.log
```

Look for `load_format: 'dummy'` in the stage_configs dump — that confirms core_model is active. With `--run-level=full_model` those entries will be absent and real weights will load.

## Verification

- Contributor **akshatvishu** independently reproduced the dummy-weight logging and provided the same diagnosis.
- Collaborator **yenuo26** confirmed the test passes on an A100 with `--run-level=full_model`.
- This issue has been closed as `invalid` (not a bug).

## Additional Notes

The test is marked `pytest.mark.full_model` (line 29 of `test_qwen3_omni.py`) because it asserts real semantic output (`"baby"`, `"book"` keywords, text-audio cosine similarity > 0.
- **state_updates**: {'draft_answer': '## Root Cause\n\nYou\'re running the test with the **default `--run-level=core_model`**, which patches every stage\'s deploy YAML to use `load_format: dummy`. This was extended to online serving in PR #4354. With dummy weights, the thinker, talker, and code2wav stages all produce garbage — hence the repeating "Joe" text and nonsensical audio (Welsh-like gibberish).\n\n**Mechanism** (code references):\n1. `tests/helpers/fixtures/run_args.py:10` — pytest `--run-level` defaults to `"core_model"`.\n2. `tests/helpers/stage_config.py:_add_dummy_load_format()` — for `core_model`, inserts `load_format: dummy` into every stage.\n3. `tests/helpers/runtime.py:iter_omni_server()` calls `stage_config_path_for_run_level()` which triggers the patch.\n4. All three stages (thinker, talker, code2wav) load with randomized dummy weights, producing the observed garbage.\n\n## Fix / Workaround\n\nPass `--run-level=full_model` to load real weights:\n\n```bash\npytest -s -v tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] --run-level=full_model\n```\n\nYou can verify dummy vs real weights by enabling `DEBUG` logging:\n\n```bash\nexport VLLM_LOGGING_LEVEL=DEBUG\npytest -s -v \\\n    tests/examples/online_serving/test_qwen3_omni.py::test_send_multimodal_request_002[omni_server0] \\\n    2>&1 | tee qwen3_test.log\n```\n\nLook for `load_format: \'dummy\'` in the stage_configs dump — that confirms core_model is active. With `--run-level=full_model` those entries will be absent and real weights will load.\n\n## Verification\n\n- Contributor **akshatvishu** independently reproduced the dummy-weight logging and provided the same diagnosis.\n- Collaborator **yenuo26** confirmed the test passes on an A100 with `--run-level=full_model`.\n- This issue has been closed as `invalid` (not a bug).\n\n## Additional Notes\n\nThe test is marked `pytest.mark.full_model` (line 29 of `test_qwen3_omni.py`) because it asserts real semantic output (`
