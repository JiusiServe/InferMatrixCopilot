# 2026-04-23 — "释放资源"只杀进程没退 srun

- 编号：`inc-2026-04-23-remote-ssh-slurm-container-04`
- 归属：`framework/remote`
- 状态：已验证
- 搜索词："释放资源"只杀进程没退 srun
- 影响范围：framework/remote

**症状**：本轮服务进程停止后，Slurm job 仍占着节点。
**根因**：只停止了应用进程，srun shell 和 allocation 生命周期仍未结束。
**解法**：按本轮记录的 PID/PGID 停止进程，退出本轮容器和 srun shell，再用 job ID 查询确认 allocation 已释放。禁止按进程名扫描或终止其他任务。
