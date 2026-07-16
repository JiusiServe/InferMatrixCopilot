# 2026-05-19 — 提交前没跑 ruff，CI 被 F841 未使用变量打回

- 编号：`inc-2026-05-19-ci-and-testing-07`
- 归属：`repos/vllm-omni/ci`
- 状态：已验证
- 搜索词：提交前没跑 ruff，CI 被 F841 未使用变量打回
- 影响范围：repos/vllm-omni/ci

**症状**：PR CI 的 `ruff check` 失败：`vllm_omni/entrypoints/openai/serving_chat.py:2583:9: F841 Local variable negative_prompt is assigned to but never used`。
**根因**：本地只跑了 `py_compile`、focused pytest 和远端功能测试，没有跑覆盖本次改动文件的 `ruff check` / pre-commit lint。新增 streaming helper 时留下了 `extra_body.get("negative_prompt")`，功能测试不触发，但 ruff 能直接抓到。
**解法**：删除未使用变量，执行 `python -m ruff check vllm_omni/entrypoints/openai/serving_chat.py vllm_omni/entrypoints/openai/api_server.py tests/entrypoints/openai_api/test_image_server.py`，再 amend + push。
**对未来的提醒**：任何提交/推 PR 前都要跑覆盖本次改动文件的 `ruff check`；如果本地有 pre-commit 环境，优先跑对应 hook。`py_compile` 和 pytest 只能证明语法/行为，不覆盖风格和未使用变量。
