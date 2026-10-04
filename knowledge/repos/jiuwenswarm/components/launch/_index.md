---
title: "启动与多实例管理"
created: 2026-09-30
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# 启动与多实例管理

- [jiuwenswarm 顶层包：启动入口、多实例与运行时补丁](jiuwenswarm.md) — start_services/jiuwenswarm-init/dotenv_early 的启动分派、端口回退持久化、子进程环境注入与就绪横幅
- [桌面端应用外壳（channels/desktop）](jiuwenswarm-channels-desktop.md)
- [instance_manager：多实例配置、端口与进程管理](jiuwenswarm-instance-manager.md) — 端口分配公式与探测语义、instances.yaml 校验、InstanceLock/GatewayLock 与安全停止阶梯

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：start_services、jiuwenswarm-start、debug launcher、multi-instance、--dotenv、--name、jiuwenswarm-init、init workspace、dotenv_early、SSE patch、ModelArts、compat alias。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| start_services、jiuwenswarm-start、debug launcher、multi-instance、--dotenv、--name、… | 入口 | `jiuwenswarm/start_services.py`、`jiuwenswarm/dotenv_early.py`、`jiuwenswarm/init_workspace.py`、`jiuwenswarm/instance_manager/` |

- [启动与实例隔离的设计取舍](design-tradeoffs.md) — 设计选择、收益与代价，以及 API、配置和关联功能入口。
- [初始化与服务启动 功能知识](feature-bootstrap.md)
- [单机多实例 功能知识](feature-instances.md)
- [桌面宿主与自动更新 功能知识](feature-desktop.md)
- [acp](acp/_index.md)
- [channels-acp](channels-acp/_index.md)
- [channels-desktop](channels-desktop/_index.md)
- [cli](cli/_index.md)
- [launch 源码接口与集成边界 01](source-contracts-01.md)
- [instance-manager](instance-manager/_index.md)
- [初始化与服务启动：实现深读](feature-depth-bootstrap.md)
- [单机多实例：实现深读](feature-depth-instances.md)
- [桌面宿主与自动更新：实现深读](feature-depth-desktop.md)
