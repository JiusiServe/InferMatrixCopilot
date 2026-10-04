---
title: "control-repositories 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# control-repositories 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/control/repositories/project_repository.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2a6c342b078f29c8c9615101ef40a1866acaaaf6463cfa52664154a7442d820a -->
**`jiuwenswarm/server/control/repositories/project_repository.py`**

- 源码对模块职责的说明：Project disk store used by Front Control.。
- 异步入口 `handle_project_request(request)`；声明返回 `AgentResponse`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from jiuwenswarm.common.schema.agent import AgentRequest, AgentResponse`；`from jiuwenswarm.common.schema.message import ReqMethod`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/control/repositories/project_repository.py#L1-L84)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/control/repositories/session_repository.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=873cc2c7d7531dd29a32fd9b56a2aa6fb0fe2bff1986e68dc8408565632de854 -->
**`jiuwenswarm/server/control/repositories/session_repository.py`**

- 源码对模块职责的说明：Session metadata store used by Front Control.。
- 异步入口 `handle_list(request)`；声明返回 `AgentResponse`。
- 异步入口 `handle_get_metadata(request)`；声明返回 `AgentResponse`。
- 异步入口 `handle_pin(request)`；声明返回 `AgentResponse`。
- 异步入口 `handle_color_set(request)`；声明返回 `AgentResponse`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from typing import Final`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/control/repositories/session_repository.py#L1-L219)。
<!-- /kb:file -->
