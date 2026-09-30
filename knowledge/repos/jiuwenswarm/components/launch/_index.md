---
title: "启动与多实例管理"
created: 2026-09-30
updated: 2026-09-30
type: index
tags: [jiuwenswarm]
sources: []
---

# 启动与多实例管理

- [jiuwenswarm 顶层包：启动入口、多实例与运行时补丁](jiuwenswarm.md)
- [桌面端应用外壳（channels/desktop）](jiuwenswarm-channels-desktop.md)
- [instance_manager：多实例配置、端口与进程管理](jiuwenswarm-instance-manager.md)

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：start_services、jiuwenswarm-start、debug launcher、multi-instance、--dotenv、--name、jiuwenswarm-init、init workspace、dotenv_early、SSE patch、ModelArts、compat alias。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| start_services、jiuwenswarm-start、debug launcher、multi-instance、--dotenv、--name、… | 入口 | `jiuwenswarm/acp/`、`jiuwenswarm/app.py`、`jiuwenswarm/channels/acp/` |
