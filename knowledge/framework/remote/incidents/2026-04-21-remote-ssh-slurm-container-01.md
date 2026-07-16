# 2026-04-21 — 假设路径 + HF 缓存丢失

- 编号：`inc-2026-04-21-remote-ssh-slurm-container-01`
- 归属：`framework/remote`
- 状态：已验证
- 搜索词：假设路径 + HF 缓存丢失
- 影响范围：framework/remote

## 原文件说明

# Error Book: 远端 SSH / Slurm / 容器基础

**症状**：docker exec 失败、挂载路径为空、HF 缓存消失
**根因**：不同节点布局不同；容器内 `~` 在容器层，非持久
**侦察三连**：
```bash
docker ps && docker inspect <container> --format '{{range .Mounts}}...'
find <AUTHORIZED_MOUNT_ROOT> -maxdepth 5 -name "snapshots" -type d 2>/dev/null
env | grep -iE "cache|hf_home"
```
**提醒**：建容器挂 `/home`，`HF_HOME` 指向持久路径
