# 2026-04-28 — pkill -f python 杀死 SSH session

- 编号：`inc-2026-04-28-profiling-and-model-loading-16`
- 归属：`repos/vllm-omni/benchmark`
- 状态：已验证
- 搜索词：pkill -f python 杀死 SSH session
- 影响范围：repos/vllm-omni/benchmark

**症状**：`ssh ... "pkill -9 -f python; ..."` 执行后 SSH 断开，exit code 255
**根因**：`pkill -f python` 匹配所有含 "python" 的进程，包括 SSH session 的子进程
**解法**：启动时记录本轮 launcher PID/PGID；清理前验证 `/proc/<pid>/cwd`、command、owner 和进程组，只停止能够证明属于本轮的进程。按脚本名搜索仍可能命中其他用户任务，不能作为清理边界。
**对未来的提醒**：远端禁止按进程名称做全局终止；没有本轮 PID/PGID 和归属证据时停止并报告。
