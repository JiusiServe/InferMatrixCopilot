---
title: "扩展与插件机制"
created: 2026-09-30
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# 扩展与插件机制

- [扩展机制与 openYuanRong 集成（jiuwenswarm/extensions/）](jiuwenswarm-extensions.md) — 扩展搜索/发现/加载顺序、registry 单例与槽位替换、hook 分发、应用插件绑定禁用门禁与 HTTP/WS/静态资源挂载约束
- [AgentOS 扩展：AgentOS Router 与 SSH/Token 鉴权](jiuwenswarm-extensions-agentos.md)
- [视频全双工扩展（video_duplex）](jiuwenswarm-extensions-video-duplex.md)

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：extension、扩展、plugin、应用插件、hook、registry、loader、manifest、yuanrong、openYuanRong、clawee、sandbox。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| extension、扩展、plugin、应用插件、hook、registry、loader、manifest、yuanrong、openYuanRong、cl… | 入口 | `jiuwenswarm/extensions/agent_client/`、`jiuwenswarm/extensions/application_host.py`、`jiuwenswarm/extensions/callback_compat.py` |

- [video_duplex 全双工扩展审查规则：任务检查点、授权投递与 Provider 协议](rules.md)

## 验证入口

扩展框架行为的单元测试在 `tests/unit_tests/test_extension_manager.py`（搜索路径、transport 标志）和 `tests/unit_tests/test_application_plugins.py`（禁用门禁、manifest-only 插件、资产路由）；`tests/unit_tests/extensions/` 下是 AgentOS 专属测试。

## 专题入口

- [应用插件绑定、前端贡献与资源挂载](jiuwenswarm-application-plugins.md) — 说明 ApplicationPlugin 的 manifest-only 构造、宿主绑定、禁用门、HTTP 资产与 WebSocket 路由；扩展发现和进程生命周期见扩展主页面。

- [扩展与应用插件的设计取舍](design-tradeoffs.md) — 设计选择、收益与代价，以及 API、配置和关联功能入口。
- [生命周期 Hooks 与扩展 功能知识](feature-hooks.md)
- [Application Plugin 与前端贡献 功能知识](feature-applications.md)
- [音视频双工扩展 功能知识](feature-video-duplex.md)
- [extensions-plugins 源码接口与集成边界 01](source-contracts-01.md)
- [agent-client](agent-client/_index.md)
- [agentos](agentos/_index.md)
- [agentos-agentos-router](agentos-agentos-router/_index.md)
- [agentos-auth](agentos-auth/_index.md)
- [sdk](sdk/_index.md)
- [video-duplex-backend](video-duplex-backend/_index.md)
- [video-duplex](video-duplex/_index.md)
- [video-duplex-frontend](video-duplex-frontend/_index.md)
