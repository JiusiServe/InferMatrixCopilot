---
title: "front 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# front 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/front/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=00a4e0e5db999bcf101fdb586df766c4d83dba81eac38a297376fc6eb17e7769 -->
**`jiuwenswarm/server/front/__init__.py`**

- 源码对模块职责的说明：Lightweight AgentServer Front: transport, protocol, router, readiness.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/front/__init__.py#L1-L17)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/front/admission.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1c53db5205a430548bab01ef847ea877ee9e097356c53db19dc63ad9191ed6fa -->
**`jiuwenswarm/server/front/admission.py`**

- 源码对模块职责的说明：Bounded queue for execution requests while Runtime is warming.。
- `RuntimeBackend` 继承 `Protocol`；方法入口：`dispatch_parsed_request`, `attach_gateway_connection`, `on_gateway_disconnect`。
- `ExecutionAdmission` 定义类型边界；方法入口：`__init__`, `backend`, `registry`, `attach_backend`, `detach_backend`, `dispatch`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from typing import Any, Protocol`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/front/admission.py#L1-L250)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/front/connection.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dbfbcb74236c6893e1b5c4d6e5a9b202ab1d795bd64ffb42ba957e5ff52f3751 -->
**`jiuwenswarm/server/front/connection.py`**

- 源码对模块职责的说明：WebSocket connection accept, origin check, and per-connection dispatch.。
- 异步入口 `process_handshake(*args)`；声明返回 `Any`。
- `ConnectionHandler` 定义类型边界；方法入口：`__init__`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/front/connection.py#L1-L145)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/front/event_forwarder.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=17d480d7bdca054587f709fabe998e07aa80bb9b92639640304de233372287ca -->
**`jiuwenswarm/server/front/event_forwarder.py`**

- 源码对模块职责的说明：Front-owned Gateway stream writer.。
- `EventForwarder` 定义类型边界；方法入口：`__init__`, `attach`, `detach`, `current_ws`, `current_send_lock`, `send`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/front/event_forwarder.py#L1-L53)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/front/protocol.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b2f6fa4d37a26ec87090625e173ebbc6b984a89e8cfbe75db351707fc28a7018 -->
**`jiuwenswarm/server/front/protocol.py`**

- 源码对模块职责的说明：Front-safe E2A parse/encode helpers. No OpenJiuwen or Agent Runtime imports.。
- 调用入口 `payload_to_request(data)`；声明返回 `AgentRequest`。
- 调用入口 `parse_raw_message(raw)`；声明返回 `AgentRequest / dict[str, Any]`。
- 调用入口 `encode_response(response, response_id)`；声明返回 `dict[str, Any]`。
- 调用入口 `encode_chunk(chunk, response_id, sequence)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/front/protocol.py#L1-L161)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/front/request_registry.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=98580f1e065a63e26ed88f8bef48bfabe608aef55baeb26ba6d1239e0d01573b -->
**`jiuwenswarm/server/front/request_registry.py`**

- 源码对模块职责的说明：Front-owned in-flight request table.。
- `TrackedRequest` 定义类型边界；方法入口：`request_id`, `session_id`。
- `RequestRegistry` 定义类型边界；方法入口：`__init__`, `register`, `mark_dispatched`, `complete`, `cancel`, `cancel_session`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import time`；`from dataclasses import dataclass, field`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/front/request_registry.py#L1-L101)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/front/router.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=78652d681bdfd0baf5ae15a022a64b7201732b1e860dc8d5c5f7b9f1b3d9b6b4 -->
**`jiuwenswarm/server/front/router.py`**

- 源码对模块职责的说明：Method router: control-plane services vs execution admission.。
- 调用入口 `is_control_method(request)`；声明返回 `bool`。
- `MethodRouter` 定义类型边界；方法入口：`__init__`, `dispatch`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from typing import Any`。
- 模块级配置或常量名称：`CONTROL_METHODS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/front/router.py#L1-L328)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/front/server.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=33e88a91305d430a507ef5abe3a825126673ce222cd6d71542ac1b07769f9423 -->
**`jiuwenswarm/server/front/server.py`**

- 源码对模块职责的说明：Lightweight AgentServer Front WebSocket listener.。
- `AgentServerFront` 定义类型边界；方法入口：`__init__`, `host`, `port`, `attach_runtime_backend`, `start`, `begin_drain`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Any`；`from jiuwenswarm.common.ws_limits import AGENT_WS_MAX_MESSAGE_BYTES`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/front/server.py#L1-L119)。
<!-- /kb:file -->
