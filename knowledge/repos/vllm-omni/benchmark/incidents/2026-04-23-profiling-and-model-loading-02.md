# 2026-04-23 — 连续跑多配置时 GPU 显存残留 OOM

- 编号：`inc-2026-04-23-profiling-and-model-loading-02`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：连续跑多配置时 GPU 显存残留 OOM
- 影响范围：repos/vllm-omni/benchmark

**症状**：tp4_fp8 跑完立即跑 tp2_sp2，OOM
**根因**：进程退出后 GPU 显存未立即释放
**解法**：每轮记录 launcher PID/PGID；结束时先验证 cwd、command 和 owner，再仅停止本轮进程组，最后用 GPU 状态确认本轮资源已释放。禁止按名称全局终止进程。
