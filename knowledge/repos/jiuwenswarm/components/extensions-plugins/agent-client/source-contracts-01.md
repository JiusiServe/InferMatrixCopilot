---
title: "agent-client 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# agent-client 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/extensions/agent_client/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=637821e0bd4f683c40b71a5da0f5020e4e45a6a40dd0e2e6b00ac7b8fe49441a -->
**`jiuwenswarm/extensions/agent_client/__init__.py`**

- 集成依赖（导入声明，不等于全部运行时依赖）：`from .extension import register_extensions`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agent_client/__init__.py#L1-L3)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/agent_client/extension.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=245bff6b41bba4d4b954be34d5d8b6367f638fee1e0329424b6f5c038e06be72 -->
**`jiuwenswarm/extensions/agent_client/extension.py`**

- 源码对模块职责的说明：AgentServerClient 扩展.。
- `YuanrongAgentServerClientExtension` 继承 `AgentServerClientExtension`；方法入口：`__init__`, `initialize`, `get_client`。
- 异步入口 `register_extensions(registry)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.common.config import get_config`；`from jiuwenswarm.extensions.sdk import AgentServerClientExtension`；`from jiuwenswarm.extensions.yuanrong_frontend_client import YuanrongFronten`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agent_client/extension.py#L1-L60)。
<!-- /kb:file -->
