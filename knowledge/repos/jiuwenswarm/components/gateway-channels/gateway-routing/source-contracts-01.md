---
title: "gateway-routing 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# gateway-routing 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/gateway/routing/agent_client.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=70666b6084e5d846e3a21aceb344423a34ccbb5dfa816add50f0f327b3196e2a -->
**`jiuwenswarm/gateway/routing/agent_client.py`**

- 源码对模块职责的说明：AgentServerClient - Gateway 与 AgentServer 的 WebSocket 客户端.。
- `AgentServerUnaryTimeout` 继承 `RuntimeError`；方法入口：`__init__`。
- `DuplicateRequestIdError` 继承 `RuntimeError`；方法入口：`__init__`。
- `WebSocketAgentServerClient` 继承 `AgentServerClient`；方法入口：`__init__`, `set_server_push_handler`, `set_disconnect_handler`, `set_or_update_server_config`, `server_ready`, `agent_ready`。
- 异步入口 `mock_agent_server_handler(ws)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import asyncio`；`import json`。
- 模块级配置或常量名称：`AGENT_REQUEST_TIMEOUT_SECONDS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/agent_client.py#L1-L841)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/routing/agent_http_bridge.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f2999889e2050453a54d208f46d0db85f4440af89c9096037b366a77e75d83c4 -->
**`jiuwenswarm/gateway/routing/agent_http_bridge.py`**

- 源码对模块职责的说明：Gateway → 目标 AgentServer 的受认证 HTTP bridge 客户端（Phase 2）。。
- 异步入口 `upload_file_bytes_via_e2a(content, target_rel_path, agent_client, user_id, channel_id, session_id)`；声明返回 `tuple[bool, dict[str, Any]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from jiuwenswarm.common.client.agent_http_bridge import UPLOAD_TIMEOUT_SECO`。
- 模块级配置或常量名称：`E2A_PAYLOAD_MAX_BYTES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/agent_http_bridge.py#L1-L100)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/routing/agent_request_timeout.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9fabae7e5ad64e11c4869e9ad099fd1a9dde14db3b64c21fdb57d7d7324a1bc9 -->
**`jiuwenswarm/gateway/routing/agent_request_timeout.py`**

- 源码对模块职责的说明：Timeout policy for Gateway -&gt; AgentServer unary requests.。
- `AgentRequestTimeoutError` 继承 `TimeoutError`；方法入口：`__init__`。
- 调用入口 `coerce_client_timeout_ms(value)`；声明返回 `int / None`。
- 调用入口 `resolve_agent_request_timeout_seconds(channel_id, method, is_stream, client_timeout_ms)`；声明返回 `float / None`。
- 调用入口 `request_timeout_from_envelope(env)`；声明返回 `float / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from typing import Any`。
- 模块级配置或常量名称：`AGENT_SERVER_TIMEOUT_CODE`, `AGENT_SERVER_TIMEOUT_ERROR`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/agent_request_timeout.py#L1-L152)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/routing/base_ws_channel.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a41924fd90f84be1443b1d34d9ff983887e404afaaf4ae560342398c61e52286 -->
**`jiuwenswarm/gateway/routing/base_ws_channel.py`**

- 源码对模块职责的说明：BaseWsChannel —— WebSocket 类 Channel 共享基类。。
- `BaseWsChannel` 继承 `BaseWebChannel`；方法入口：`__init__`, `set_channel_event_reporter`, `report_connect`, `report_disconnect`, `register_ws`, `unregister_ws`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/base_ws_channel.py#L1-L410)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/routing/e2a_proxy.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=224dff2441c6ecf51666d4d84976ebafaa5c9233078ca640e18650cc561b34e9 -->
**`jiuwenswarm/gateway/routing/e2a_proxy.py`**

- 源码对模块职责的说明：Gateway → AgentServer 统一薄代理（E2A 转发）。。
- 调用入口 `is_agentos_routing_client(agent_client)`；声明返回 `bool`。
- 调用入口 `is_legacy_shared_directory_client(agent_client)`；声明返回 `bool`。
- 异步入口 `proxy_unary_request(channel, agent_client, ws, req_id, params, session_id, user_id, req_method, label, timeout_seconds, …)`；声明返回 `bool`。
- 异步入口 `fetch_agent_unary(agent_client, req_method, params, session_id, user_id, channel_id, label, timeout_seconds)`；声明返回 `tuple[bool, dict[str, Any]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import time`；`import uuid`。
- 模块级配置或常量名称：`SERVICE_UNAVAILABLE_CODE`, `DEFAULT_PROXY_LABEL`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/e2a_proxy.py#L1-L378)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/routing/interaction_context.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d91bb20099bc76f7f154ee4a3413f7d252af4e60929b841332ae119c3d8ea52f -->
**`jiuwenswarm/gateway/routing/interaction_context.py`**

- 源码对模块职责的说明：PendingInteraction — 统一的追问上下文，支持群聊追问和 DM 追问两种模式。。
- `PendingInteraction` 定义类型边界；方法入口：`save`, `remove`, `load`, `find_pending`, `find_all_group_pending`, `find_group_pending`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import glob`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/interaction_context.py#L1-L189)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/routing/keys.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1394da50f33db769f9f0d5d3d5b4ae132d1952d422565f6f1dd0d853318954d8 -->
**`jiuwenswarm/gateway/routing/keys.py`**

- 源码对模块职责的说明：路由核心值对象：5 维路由键、Agent 标识、Channel 索引、物理投递地址.。
- `AgentRef` 定义类型边界；方法入口：`default`。
- `RoutingKey` 定义类型边界；方法入口：`channel_key`, `identity`, `to_dict`。
- `ChannelKey` 定义类型边界。
- `IdentityKey` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass, field`；`from typing import Any`。
- 模块级配置或常量名称：`WILDCARD`, `APP_ID_DEFAULT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/keys.py#L1-L394)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/routing/route_binding.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2a637121679db20b2bcd545da43633c89df35c181f84ae70f0b415ea28888fd8 -->
**`jiuwenswarm/gateway/routing/route_binding.py`**

- `GatewayRouteBinding` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from typing import Any, Awaitable, Callable`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/route_binding.py#L1-L22)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/routing/session_map.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7b352cb28c9b541efdd7ecf1a447aee5f468ca65724a68c130bd4103ba0ce94d -->
**`jiuwenswarm/gateway/routing/session_map.py`**

- `SessionMapScope` 继承 `str, Enum`。
- 调用入口 `load_session_map_scope()`；声明返回 `SessionMapScope`。
- `SessionMap` 定义类型边界；方法入口：`__init__`, `get_session_id`, `find_session_id`, `set_session_id`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from enum import Enum`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/session_map.py#L1-L115)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/routing/session_sharing.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=885a557cdded0f6c28f2fdf1eb5c68509b9a0d57801899fae5ab57ecafe94b57 -->
**`jiuwenswarm/gateway/routing/session_sharing.py`**

- 源码对模块职责的说明：共享会话订阅表 + 分发意图 + 响应分发入口.。
- `SubRole` 定义类型边界。
- `Subscription` 定义类型边界；方法入口：`identity`, `is_godview`。
- `LogicalTarget` 定义类型边界。
- `RoutingTarget` 定义类型边界；方法入口：`from_logical`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`import time`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/session_sharing.py#L1-L579)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/routing/third_agent.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=194e52cbb8899e1df04713bfccaf423e62e1041ec3308983bc0f6af3e8f64c81 -->
**`jiuwenswarm/gateway/routing/third_agent.py`**

- 源码对模块职责的说明：ThirdAgent - 第三方 Agent list/switch 能力接口.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.common.client.third_agent import ThirdAgent, UnsupportedTh`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/routing/third_agent.py#L1-L17)。
<!-- /kb:file -->
