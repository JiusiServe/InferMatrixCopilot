# 2026-04-28 — 用户要 torch profiler trace，给了 benchmark stats JSON

- 编号：`inc-2026-04-28-profiling-and-model-loading-10`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：用户要 torch profiler trace，给了 benchmark stats JSON
- 影响范围：repos/vllm-omni/benchmark

**症状**：用户说"我要的是每个算子的细节，我要那种可以时序图的json"
**根因**：只跑了 `run_diffusion_profiling.sh` 的 Phase 1（stage_durations benchmark），没跑 Phase 2（torch profiler trace）
**解法**：用 `--profiler-config` 参数启动 server，发请求后 `/start_profile` + `/stop_profile` 收集 `trace_rank*.json.gz`
**对未来的提醒**：profiling 有两种产物——benchmark stats（吞吐/延迟/stage duration）和 torch trace（算子级时序图），确认用户要哪种
