# 2026-04-27 — 新登录节点 srun 不在 PATH，需 module load

- 编号：`inc-2026-04-27-remote-ssh-slurm-container-06`
- 归属：`framework/remote`
- 状态：已验证
- 搜索词：新登录节点 srun 不在 PATH，需 module load
- 影响范围：framework/remote

**症状**：`bash: line 1: srun: command not found`
**根因**：部分登录节点用 Environment Modules 管理 Slurm
**解法**：`source /etc/profile && module load slurm/slurm/23.02.7 && srun ...`
**提醒**：进新登录节点先 `module avail 2>&1 | grep -i slurm` 确认模块名
