# 2026-04-22 — GEBench test 未传 --samples-per-type

- 编号：`inc-2026-04-22-ci-and-testing-09`
- 归属：`repos/vllm-omni/ci`
- 状态：已验证
- 搜索词：GEBench test 未传 --samples-per-type
- 影响范围：repos/vllm-omni/ci

**症状**：pytest 传了参数但测试函数没透传，跑了全量数据集
**解法**：测试函数接收 fixture 并传给 `gbench_main`
**提醒**：GEBench 每样本 6 张图，smoke test 用 `--samples-per-type 1`
