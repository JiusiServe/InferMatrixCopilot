---
title: "公共基础模块与配置"
created: 2026-09-30
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# 公共基础模块与配置

- [jiuwenswarm/common/：公共基础模块](jiuwenswarm-common.md) — config.yaml 读写、模型目录与选择持久化、目录校验/连通性探测、permissions 与 MCP 配置面
- [ACP stdio 客户端（common/acp）](jiuwenswarm-common-acp.md)
- [配置面板 handler（config_panel）](jiuwenswarm-common-config-panel.md) — Web/TUI config/models handler；provider 归一化与 reasoning 档位的序列化/校验
- [公共 Schema：Agent 请求响应、统一消息与参数契约](jiuwenswarm-common-schema.md)

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：common、config、配置、模型选择、model catalog、mode、工作区、cron、updater、doctor、hooks、kv cache。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| common、config、配置、模型选择、model catalog、mode、工作区、cron、updater、doctor、hooks、kv cache… | 入口 | `jiuwenswarm/common/config.py`、`jiuwenswarm/common/model_catalog.py`、`jiuwenswarm/common/mcp_config.py`、`jiuwenswarm/common/_build_config.py` |

- [jiuwenswarm/common 审查规则：配置读写事务、跨仓契约与持久化键稳定性](rules.md)

## 专题入口

- [模型目录、稳定选择与配置校验](jiuwenswarm-common-model-catalog.md) — 说明共享配置模型的稳定业务 ID、目录视图、选择 DTO、候选写入与校验；登录凭据的产生和续期由 login-auth 拥有。
