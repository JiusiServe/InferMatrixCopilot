---
title: "agent-server-runtime 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# agent-server-runtime 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e7bf7b871c129c6453c75818953c1a4f1b0e25b12dc834b05d2f1a84c500550e -->
**`jiuwenswarm/server/__init__.py`**

- 源码对模块职责的说明：AgentServer 模块.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import TYPE_CHECKING, Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/__init__.py#L1-L25)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/agent_ws_server.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1bcc8c158af265497f3796cd20826d1de0fa75d87e860770e929ef163032ee5b -->
**`jiuwenswarm/server/agent_ws_server.py`**

- 源码对模块职责的说明：AgentWebSocketServer - Gateway 与 AgentServer 之间的 WebSocket 服务端.。
- `McpUpsertTypes` 继承 `NamedTuple`。
- `AgentWebSocketServer` 定义类型边界；方法入口：`__init__`, `set_proactive_engine`, `set_runtime_lifecycle_hooks`, `set_rsi_harness_provider`, `get_instance`, `reset_instance`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import datetime as _dt`；`import inspect`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/agent_ws_server.py#L1-L12356)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/lifecycle.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f8a75767df17c424cc405bb42443f0ea0b6b6b79d3a7b15e30815b39a8676d39 -->
**`jiuwenswarm/server/lifecycle.py`**

- 源码对模块职责的说明：AgentServer readiness state machine for the Front / Runtime split.。
- `ReadinessState` 继承 `str, Enum`。
- `Readiness` 定义类型边界；方法入口：`__init__`, `state`, `snapshot`, `mark_transport_ready`, `mark_control_ready`, `mark_runtime_warming`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`from enum import Enum`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/lifecycle.py#L1-L161)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/wire_truncate.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=24134cd04a4e44db63410f6ed62859b10ec5065af7df560d2dfc1936c1af3eea -->
**`jiuwenswarm/server/wire_truncate.py`**

- 源码对模块职责的说明：Wire-payload truncation for the AgentWebSocketServer.。
- 调用入口 `split_history_record_for_stream(record, part_bytes)`；声明返回 `list[dict[str, Any]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/wire_truncate.py#L1-L770)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/ws_send.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b7483671c22d59b3b1b0c72741488374f0eeea585167ecf2e75a7594bed15960 -->
**`jiuwenswarm/server/ws_send.py`**

- 源码对模块职责的说明：Bounded WebSocket wire sending for AgentServer responses.。
- 异步入口 `send_wire_payload(ws, wire)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/ws_send.py#L1-L131)。
<!-- /kb:file -->
