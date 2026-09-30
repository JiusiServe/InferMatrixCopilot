---
title: "扩展与插件机制"
created: 2026-09-30
updated: 2026-09-30
type: index
tags: [jiuwenswarm]
sources: []
---

# 扩展与插件机制

- [扩展机制与 openYuanRong 集成（jiuwenswarm/extensions/）](jiuwenswarm-extensions.md)
- [AgentOS 扩展：AgentOS Router 与 SSH/Token 鉴权](jiuwenswarm-extensions-agentos.md)
- [视频全双工扩展（video_duplex）](jiuwenswarm-extensions-video-duplex.md)

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：extension、扩展、plugin、应用插件、hook、registry、loader、manifest、yuanrong、openYuanRong、clawee、sandbox。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| extension、扩展、plugin、应用插件、hook、registry、loader、manifest、yuanrong、openYuanRong、cl… | 入口 | `jiuwenswarm/extensions/agent_client/`、`jiuwenswarm/extensions/application_host.py`、`jiuwenswarm/extensions/callback_compat.py` |
