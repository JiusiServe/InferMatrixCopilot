---
title: "NFS 部署脚本（scripts/nfs）"
created: 2026-10-05
updated: 2026-10-05
type: architecture
tags: [jiuwenswarm]
sources: []
---

# NFS 部署脚本（scripts/nfs）

提供在服务器与客户端上安装和卸载 NFS 共享存储的 bash 脚本，用于多实例部署时挂载共享目录。四个脚本分别覆盖服务端/客户端的 setup 与 teardown。

**入口脚本**

- `scripts/nfs/setup_nfs_server.sh` — 在服务端安装并导出 NFS 共享目录，先读这个了解配置的共享路径与导出参数
- `scripts/nfs/setup_nfs_client.sh` — 在客户端挂载服务端导出的 NFS 目录

**其余脚本**

- `scripts/nfs/teardown_nfs_server.sh` — 服务端卸载：取消导出并清理 NFS 服务
- `scripts/nfs/teardown_nfs_client.sh` — 客户端卸载：解除挂载并清理

**相关文档**

- `README_CN.md` — 安装与部署总览，了解 NFS 脚本在部署流程中的位置
- `docs/README.md` — 文档总导航，定位多实例/部署相关文档

**Routes**

- `scripts/nfs/`
