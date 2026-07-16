# 2026-04-27 — Windows ControlMaster 不可用，ASKPASS 触发 fail2ban

- 编号：`inc-2026-04-27-remote-ssh-slurm-container-05`
- 归属：`framework/remote`
- 状态：已验证
- 搜索词：Windows ControlMaster 不可用，ASKPASS 触发 fail2ban
- 影响范围：framework/remote

**症状**：ControlMaster 报 `getsockname failed: Not a socket`；密码认证连续失败后被封禁
**根因**：Windows Git Bash / OpenSSH ControlMaster 均不支持；WSL2 NAT 无法访问内网段；ASKPASS 失败触发 fail2ban
**解法**：用 `/c/Windows/System32/OpenSSH/ssh.exe` + SSH key auth + 重试逻辑（5次×3s）；每次 SSH 打包多条命令
**提醒**：服务器 `MaxStartups` 限制并发，快速连多次随机拒绝；key auth 不触发 fail2ban
