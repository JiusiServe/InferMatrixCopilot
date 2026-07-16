# 2026-04-28 — vllm-omni profiler delay_iterations:1 + 单请求 → 空 trace

- 编号：`inc-2026-04-28-profiling-and-model-loading-15`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：vllm-omni profiler delay_iterations:1 + 单请求 → 空 trace
- 影响范围：repos/vllm-omni/benchmark

**症状**：trace 文件只有 21-25KB，profiler_out 只有 2 个调用（cudaDeviceSynchronize + Activity Buffer Request）
**根因**：profiler config `delay_iterations:1` 跳过第一个 step()，但只发了 1 个请求，所以 profiler 跳过了唯一的请求
**解法**：`delay_iterations:0`，让 profiler 立即开始录制 → 47MB/rank trace
**对未来的提醒**：单请求 profiling 时 `delay_iterations` 必须为 0
