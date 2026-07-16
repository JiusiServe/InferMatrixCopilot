# 2026-04-27 — srun --pty 在非交互 SSH 下报 ioctl 错误但仍能执行

- 编号：`inc-2026-04-27-remote-ssh-slurm-container-07`
- 归属：`framework/remote`
- 状态：已验证
- 搜索词：srun --pty 在非交互 SSH 下报 ioctl 错误但仍能执行
- 影响范围：framework/remote

**症状**：`srun: error: ioctl(TIOCGWINSZ): Inappropriate ioctl for device` + `Not using a pseudo-terminal, disregarding --pty option`
**根因**：通过 `ssh host 'cmd'` 非交互方式调用 srun，没有 TTY，--pty 无效
**结论**：不影响命令执行，输出仍然正常返回；忽略这两行错误即可
**提醒**：需要真正交互式 shell 时必须用 tmux，不能靠 ssh host 'srun --pty bash'
