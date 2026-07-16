# 2026-04-23 — multiprocessing spawn 子进程 cwd PermissionError

- 编号：`inc-2026-04-23-remote-ssh-slurm-container-03`
- 归属：`framework/remote`
- 状态：已验证
- 搜索词：multiprocessing spawn 子进程 cwd PermissionError
- 影响范围：framework/remote

**症状**：worker 进程启动即崩，父进程报 `EOFError`
**根因**：spawn 模式 `os.chdir()` 到父进程 cwd（Lustre 目录），容器 root 没权限
**解法**：跑命令前 `cd /tmp`
**提醒**：EOFError 时先找 worker 端真正错误
