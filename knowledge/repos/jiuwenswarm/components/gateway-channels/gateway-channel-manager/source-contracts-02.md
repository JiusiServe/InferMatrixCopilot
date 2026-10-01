---
title: "gateway-channel-manager 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# gateway-channel-manager 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/media.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a37357f26c30fc26b4695dd462bdfa046ba804020953bfb8c5d823ab9a8c2529 -->
**`jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/media.py`**

- 源码对模块职责的说明：XiaoYi Media Utils - 媒体下载、处理和保存功能。 基于 TypeScript xiaoyi-media.ts 实现。。
- `MediaDownloadOptions` 定义类型边界。
- `DownloadedMedia` 定义类型边界。
- `MediaFile` 定义类型边界。
- 调用入口 `is_image_mime_type(mime_type)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import asyncio`；`import base64`；`from dataclasses import dataclass`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/media.py#L1-L353)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc13f7ef26359e5788a945a3a74c02260ce474d86557b45bf0968f2cc3fdf9dc -->
**`jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py`**

- 源码对模块职责的说明：XiaoYi Push Message Service - 主动推送消息服务.。
- `PushConfig` 定义类型边界。
- `XiaoYiPushService` 定义类型边界；方法入口：`__init__`, `send_push`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import logging`；`import base64`；`import hashlib`；`import hmac`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py#L1-L132)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/tui/tui_channel.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4292ef5f1844b77ce59a5c90dfc17106f764ceb6360cb32908434af0052e833f -->
**`jiuwenswarm/gateway/channel_manager/tui/tui_channel.py`**

- 源码对模块职责的说明：TuiChannel —— TUI 终端 WebSocket 通道（出站契约 + 五维索引）.。
- `TuiChannelConfig` 定义类型边界。
- `TuiChannel` 继承 `BaseWsChannel`；方法入口：`__init__`, `on_message`, `start`, `stop`, `send`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`from dataclasses import dataclass`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/tui/tui_channel.py#L1-L270)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/tui/tui_connect.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3b514c424c08f1bf88a056481d90d47db5bbba741f4f7539cf7c333924d70c61 -->
**`jiuwenswarm/gateway/channel_manager/tui/tui_connect.py`**

- `CliHandlersBindParams` 定义类型边界。
- `CliRouteBindParams` 定义类型边界。
- `ForwardRewindE2AParams` 定义类型边界。
- 调用入口 `resolve_tui_session_project_path(session)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import contextlib`；`import logging`。
- 模块级配置或常量名称：`CLI_FORWARD_REQ_METHODS`, `CLI_FORWARD_NO_LOCAL_HANDLER_METHODS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/tui/tui_connect.py#L1-L2728)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=837587aae1da6f890922a2ee54f6d5d20d703226275854a666d782ffd6069615 -->
**`jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py`**

- 源码对模块职责的说明：WebChannel RPC handlers and shared constants (used by app gateway; single source with app.py).。
- `WebHandlersBindParams` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import importlib.util`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/app_web_handlers.py#L1-L5794)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/web/container_file_http.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=124e653661a8b68bedf8eb3c7603cc703d6dda8647bbae5125b52e94a1946cf6 -->
**`jiuwenswarm/gateway/channel_manager/web/container_file_http.py`**

- 源码对模块职责的说明：Gateway WebChannel ''/file-api'' HTTP routes (agentos_router, same port as ''/ws'').。
- `RawFileQuery` 继承 `BaseModel`。
- `FileContentGetQuery` 继承 `BaseModel`。
- `ListFilesQuery` 继承 `BaseModel`。
- `UploadForm` 继承 `BaseModel`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import base64`；`import json`；`import logging`。
- 模块级配置或常量名称：`FILE_API_PREFIX`, `MAX_UPLOAD_COUNT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/container_file_http.py#L1-L1078)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/web/git_ws_handler.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=13d27e192106bef58a6f61891df8a255fc546359995d4f553c8d100289c4635b -->
**`jiuwenswarm/gateway/channel_manager/web/git_ws_handler.py`**

- 源码对模块职责的说明：GitDiffWebSocketHandler: /ws/git 路由的消息分发与推送(设计文档 §2.6 / §4.2)。。
- `GitDiffWebSocketHandler` 定义类型边界；方法入口：`__init__`, `handle_connection`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import time`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/git_ws_handler.py#L1-L596)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/web/lifecycle_handlers.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6e6d4d1ea6fb9aa821786d8d97a6444829329901700b9edbfd8e5e77057f99e4 -->
**`jiuwenswarm/gateway/channel_manager/web/lifecycle_handlers.py`**

- 源码对模块职责的说明：Gateway lifecycle orchestration: archive checks state; deletion stops work.。
- 调用入口 `register_lifecycle_handlers(channel, resolve_client, resolve_cron)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from jiuwenswarm.common.schema.message import ReqMethod`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/lifecycle_handlers.py#L1-L172)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/web/task_asr.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=25cda29bf73ec9114c5039c6191dd20f8970517d284a96e0e7758abdef6c2c82 -->
**`jiuwenswarm/gateway/channel_manager/web/task_asr.py`**

- 源码对模块职责的说明：OpenAI-compatible ASR used by the regular task chat composer.。
- `TaskAsrError` 继承 `RuntimeError`；方法入口：`__init__`。
- 调用入口 `task_asr_endpoint(api_base)`；声明返回 `str`。
- 异步入口 `transcribe_task_audio(params, environ, client)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import base64`；`import binascii`；`import os`。
- 模块级配置或常量名称：`MAX_TASK_ASR_AUDIO_BYTES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/task_asr.py#L1-L173)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/web/trajectory_http.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5f2ead17ff1fae0010c833801e1bad16e6efa48ebd14c5e51b119ab0f2873ea8 -->
**`jiuwenswarm/gateway/channel_manager/web/trajectory_http.py`**

- 源码对模块职责的说明：Gateway HTTP read API for persisted single-Agent trajectory records.。
- `TrajectoryHttpService` 定义类型边界；方法入口：`__init__`, `settings`, `reader`, `list_subjects`, `export_archive`, `get_session_usage`。
- 调用入口 `attach_trajectory_routes(app, channel, settings, reader, metadata_loader)`；声明返回 `TrajectoryHttpService`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import io`；`import json`。
- 模块级配置或常量名称：`TRAJECTORY_API_PREFIX`, `TRAJECTORY_ARCHIVE_ENTRY_NAME`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/trajectory_http.py#L1-L970)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/web/web_connect.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2df5f67cf28895bf0c6acad0908d474a0ed53e2241612d6ff7b66fa9f60ffd29 -->
**`jiuwenswarm/gateway/channel_manager/web/web_connect.py`**

- 源码对模块职责的说明：WebChannel - WebSocket 通道实现.。
- `WebChannelConfig` 定义类型边界。
- `WebChannel` 继承 `BaseWsChannel`；方法入口：`__init__`, `clients`, `register_method`, `unregister_method`, `on_message`, `wrap_message_callback`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import inspect`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/web_connect.py#L1-L1838)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/web/web_http_auth.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=591e9b2fb513f09b7f6c6cb67e29d3d17ee44156c5b1f9025cd91d21cbb1e926 -->
**`jiuwenswarm/gateway/channel_manager/web/web_http_auth.py`**

- 源码对模块职责的说明：Gateway Web HTTP 的登录路由（''/api/v1/auth/*''），华为账号 Account Kit。。
- `AuthClaimBody` 继承 `BaseModel`。
- `AuthCallbackQuery` 继承 `BaseModel`。
- 调用入口 `resolve_session_id(request)`；声明返回 `str / None`。
- 调用入口 `register_auth_routes(app)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import html`；`import logging`；`from typing import Annotated`。
- 模块级配置或常量名称：`AUTH_SESSION_COOKIE`, `AUTH_SESSION_HEADER`, `AUTH_CALLBACK_CHANNEL`, `AUTH_CALLBACK_MESSAGE`, `AUTH_REQUEST_HEADER`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/web_http_auth.py#L1-L349)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/web/ws_connection_adapter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a321293f63c9148672e7ede66c5690f4c434d6972ef50a971ff885743bbbc12d -->
**`jiuwenswarm/gateway/channel_manager/web/ws_connection_adapter.py`**

- 源码对模块职责的说明：Adapt Starlette WebSocket to the websockets-like surface WebChannel expects.。
- `StarletteWsAdapter` 定义类型边界；方法入口：`__init__`, `closed`, `state`, `accept`, `send`, `recv`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketS`；`from websockets.exceptions import ConnectionClosed, ConnectionClosedError, `。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/ws_connection_adapter.py#L1-L116)。
<!-- /kb:file -->
