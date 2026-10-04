---
title: "extensions-plugins 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# extensions-plugins 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/extensions/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=65937a7e9933cb819ba8770196610b4106ddf6b05d7cf09504ae0062c88e431e -->
**`jiuwenswarm/extensions/__init__.py`**

- 源码对模块职责的说明：Extension public surface with transport adapters loaded lazily.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from importlib import import_module`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/__init__.py#L1-L48)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/clawee.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7e1cd59b5c2e3008e7dbacbab35d2ee05cc64c4467aa0107935c65e1eddd2de5 -->
**`jiuwenswarm/extensions/clawee.py`**

- 源码对模块职责的说明：OpenYuanRong 函数入口 - clawee handler.。
- 调用入口 `payload_to_request(request)`；声明返回 `AgentRequest`。
- 调用入口 `to_json(msg)`；声明返回 `str`。
- 调用入口 `chunk_to_payload(chunk)`；声明返回 `str`。
- 调用入口 `response_to_payload(resp)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import asyncio`；`import json`；`import threading`；`from concurrent.futures import Future`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/clawee.py#L1-L339)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/hook_event.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=20f93617c0472bdbedcaaec362ea4b51da674a88382731e7844d06c5066693dc -->
**`jiuwenswarm/extensions/hook_event.py`**

- `GatewayHookEvents` 继承 `HookEventBase`。
- `AgentServerHookEvents` 继承 `HookEventBase`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.common.schema.event_base import HookEventBase`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/hook_event.py#L1-L30)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/hooks_context.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d29d881787368d991f3f9b70af2194240b97b7f35cc066e6917076e6d758378d -->
**`jiuwenswarm/extensions/hooks_context.py`**

- `MemoryHookContext` 定义类型边界；方法入口：`to_dict`。
- `GatewayChatHookContext` 定义类型边界；方法入口：`to_dict`。
- `AgentServerChatHookContext` 定义类型边界；方法入口：`to_dict`。
- `SystemPromptHookContext` 定义类型边界；方法入口：`to_dict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import asdict, dataclass, field`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/hooks_context.py#L1-L60)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/types.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=909de843354eda044e9fbca685123fb0e3e92ff8c2e1eda20cf38f35ba24a64a -->
**`jiuwenswarm/extensions/types.py`**

- `ExtensionMetadata` 定义类型边界。
- `ExtensionConfig` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/types.py#L1-L26)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/yuanrong_frontend_client.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=257d2aac0e7c52412048d99849704482b38aae2950ca4f1dc9a9b56bbd451f6b -->
**`jiuwenswarm/extensions/yuanrong_frontend_client.py`**

- 源码对模块职责的说明：YuanrongFrontendAgentClient - openYuanRong Frontend HTTP 客户端.。
- 调用入口 `normalize_trace_id(value)`；声明返回 `str`。
- 调用入口 `bind_southbound_trace_id(value)`；声明返回 `str`。
- 调用入口 `current_southbound_trace_id()`；声明返回 `str`。
- 调用入口 `clear_southbound_trace_id()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`import logging`。
- 模块级配置或常量名称：`TRACE_ID_HEADER`, `DEFAULT_RUNTIME_PROBE_SETTINGS`, `DEFAULT_THIRD_AGENT_PROBE_SETTINGS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/yuanrong_frontend_client.py#L1-L2028)。
<!-- /kb:file -->
