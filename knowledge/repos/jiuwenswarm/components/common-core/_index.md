---
title: "公共基础模块与配置"
created: 2026-09-30
updated: 2026-09-30
type: index
tags: [jiuwenswarm]
sources: []
---

# 公共基础模块与配置

- [jiuwenswarm/common/：公共基础模块](jiuwenswarm-common.md)
- [ACP stdio 客户端（common/acp）](jiuwenswarm-common-acp.md)
- [配置面板 handler（config_panel）](jiuwenswarm-common-config-panel.md)
- [公共 Schema：Agent 请求响应、统一消息与参数契约](jiuwenswarm-common-schema.md)

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：common、config、配置、模型选择、model catalog、mode、工作区、cron、updater、doctor、hooks、kv cache。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| common、config、配置、模型选择、model catalog、mode、工作区、cron、updater、doctor、hooks、kv cache… | 入口 | `jiuwenswarm/common/_build_config.py`、`jiuwenswarm/common/chat_final.py`、`jiuwenswarm/common/cleanup.py` |

- [jiuwenswarm/common 审查规则：配置读写事务、跨仓契约与持久化键稳定性](rules.md)
