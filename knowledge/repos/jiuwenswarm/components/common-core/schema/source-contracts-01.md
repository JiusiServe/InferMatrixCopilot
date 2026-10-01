---
title: "schema 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# schema 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/common/schema/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3f166b90082d0022c14e200a4017a2574e002b2bbde4917fa0486fc608b41f85 -->
**`jiuwenswarm/common/schema/__init__.py`**

- 源码对模块职责的说明：数据模型.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.common.schema.agent import AgentRequest, AgentResponse, Ag`；`from jiuwenswarm.common.schema.message import Message`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/schema/__init__.py#L1-L13)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/schema/agent.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8f531415adb964d280ae598a499742897e6cbf891265fd083a873e6aba4e588c -->
**`jiuwenswarm/common/schema/agent.py`**

- 源码对模块职责的说明：Agent 请求与响应模型.。
- `PermissionContext` 定义类型边界；方法入口：`scene`, `owner_scope_key`, `to_dict`, `from_dict`。
- `AgentRequest` 定义类型边界。
- `AgentResponse` 定义类型边界。
- `AgentResponseChunk` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass, field`；`from typing import Any`；`from jiuwenswarm.common.schema.message import ReqMethod`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/schema/agent.py#L1-L122)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/schema/chat_send.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=896ef507b01c54dcfc8a96c22c0e7074c3f954fc1bd02df8a60a36f834c4cad8 -->
**`jiuwenswarm/common/schema/chat_send.py`**

- 源码对模块职责的说明：chat.send 参数契约。。
- `ChatSendParams` 继承 `TypedDict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from typing import TypedDict, NotRequired`。
- 模块级配置或常量名称：`PLAN_ENTRY_SOURCE_SLASH_COMMAND`, `PLAN_ENTRY_SOURCE_PLAN_TOGGLE`, `PLAN_ENTRY_SOURCES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/schema/chat_send.py#L1-L203)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/schema/event_base.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=48600551ac5879afb349b17942e08bcf175b532e7630729139ae6b0ab4b1435a -->
**`jiuwenswarm/common/schema/event_base.py`**

- 源码对模块职责的说明：与 openjiuwen 0.1.9+ ''openjiuwen.core.runner.callback.events'' 中 EventBase 对齐的最小 HookEventBase。。
- 调用入口 `build_event_name(scope, event_name)`；声明返回 `str`。
- 调用入口 `parse_event_name(scoped_event)`；声明返回 `tuple[str, str]`。
- `HookEventBase` 定义类型边界；方法入口：`get_event`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`。
- 模块级配置或常量名称：`DEFAULT_SCOPE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/schema/event_base.py#L1-L41)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/schema/message.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0ae647fe65837592a4f9a0f74fb9672b65cbc1557e291bad2acc5fd0398e24c6 -->
**`jiuwenswarm/common/schema/message.py`**

- 源码对模块职责的说明：统一消息模型.。
- `ReqMethod` 继承 `Enum`。
- `EventType` 继承 `Enum`。
- `Mode` 继承 `Enum`；方法入口：`from_raw`, `to_runtime_mode`。
- `Message` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import logging`；`from dataclasses import dataclass`；`from enum import Enum`；`from typing import Any, Literal`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/schema/message.py#L1-L628)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/schema/swarmflow_reply.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=381389be7cfe964ed6cbfa82c2268a62d2d8f5c628b068eadc48013726d3bf06 -->
**`jiuwenswarm/common/schema/swarmflow_reply.py`**

- 源码对模块职责的说明：chat.swarmflow_reply 参数契约。。
- `SwarmflowReplyParams` 继承 `TypedDict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from typing import TypedDict`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/schema/swarmflow_reply.py#L1-L31)。
<!-- /kb:file -->
