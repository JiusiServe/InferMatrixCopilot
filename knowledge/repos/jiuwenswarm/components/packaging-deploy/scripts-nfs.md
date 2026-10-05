---
title: "NFS 共享工作区脚本 (scripts/nfs/)"
created: 2026-10-05
updated: 2026-10-05
type: architecture
tags: [jiuwenswarm]
sources: []
---

# NFS 共享工作区脚本 (scripts/nfs/)

提供在多机部署中为 jiuwen_team 共享工作区搭建和拆除 NFS 服务端/客户端的运维脚本。四个脚本均需 sudo 手动执行，默认路径为 ${JIUWEN_TEAM_WORKSPACE_ROOT:-/tmp/jiuwenswarm/shared_workspace/jiuwen_team}。

**入口脚本**

- `scripts/nfs/setup_nfs_server.sh` — 服务端入口：安装 nfs 服务包、写入 /etc/exports.d/jiuwenswarm.exports、exportfs -rav、启用服务并做本地 bind 挂载
- `scripts/nfs/setup_nfs_client.sh` — 客户端入口：安装 nfs 客户端包、备份已有本地工作区、mount -t nfs4 并持久化到 /etc/fstab

**拆除脚本**

- `scripts/nfs/teardown_nfs_server.sh` — 删除导出文件并 exportfs -rav；可选 --stop-service/--disable-service/--remove-bind-fstab
- `scripts/nfs/teardown_nfs_client.sh` — umount 挂载点并经内嵌 python3 清理 /etc/fstab 的 nfs4 行（先备份 fstab），支持 --clean-all-server-entries

**相关文档**

- `docs/zh/AgentTeam.md` — 了解这些脚本服务的 jiuwen_team 多机协作背景时读
- `README_CN.md` — 仓库总体介绍与安装入口

**Routes**

- `scripts/nfs/`
