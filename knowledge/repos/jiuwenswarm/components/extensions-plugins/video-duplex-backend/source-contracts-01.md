---
title: "video-duplex-backend 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# video-duplex-backend 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=42b66e202e876726ffd8a4dda6f57b57f7e4ce6f339664c1161acb948f826dc0 -->
**`jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py`**

- 源码对模块职责的说明：JoyAI-specific video, action, ASR, and TTS protocol adapters.。
- `JoyAIRateLimitError` 继承 `RuntimeError`。
- 调用入口 `model_config()`；声明返回 `tuple[str, str, str]`。
- 调用入口 `voice_config()`；声明返回 `tuple[str, str, str]`。
- 调用入口 `uses_native_voice_channel(video_live_mode)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`from array import array`；`import base64`。
- 模块级配置或常量名称：`MAX_FRAME_CHARS`, `MAX_INSTRUCTION_CHARS`, `MAX_TOOL_CONTEXT_CHARS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/joyai_provider.py#L1-L464)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/qwen_omni_gateway.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f70bfd81ccf50e3f0140c98c9cd927507aa8cb4d2cf6c345f64bc0a91a0b431a -->
**`jiuwenswarm/extensions/video_duplex/backend/qwen_omni_gateway.py`**

- 源码对模块职责的说明：Authenticated WebSocket relay for Alibaba Cloud Qwen-Omni Realtime.。
- `QwenOmniRealtimeConfig` 定义类型边界；方法入口：`from_environment`, `validate`, `upstream_with_model`。
- 异步入口 `serve_qwen_omni_websocket(websocket)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`from dataclasses import dataclass`；`import json`。
- 模块级配置或常量名称：`QWEN_OMNI_PROXY_PATH`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/qwen_omni_gateway.py#L1-L175)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/qwen_omni_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6b4c306e58a1bc1245cc4910091d798fbe2ce4940a2ee306a338e4d43a025d70 -->
**`jiuwenswarm/extensions/video_duplex/backend/qwen_omni_tools.py`**

- 源码对模块职责的说明：Qwen Omni Realtime tool definitions and request validation.。
- `QwenOmniToolCall` 定义类型边界；方法入口：`query`。
- 调用入口 `qwen_omni_tools()`；声明返回 `list[dict[str, Any]]`。
- 调用入口 `parse_qwen_omni_tool_call(value)`；声明返回 `QwenOmniToolCall`。
- 调用入口 `task_management_tools()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`import json`；`from typing import Any`。
- 模块级配置或常量名称：`QWEN_OMNI_DELEGATE_TOOL_NAME`, `QWEN_OMNI_RESEARCH_TOOL_NAME`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/qwen_omni_tools.py#L1-L306)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/settings.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ca04048ac35993a10ebd29b3fe457b5aeeb5804cc6bd9052d58aded5b6ff98b0 -->
**`jiuwenswarm/extensions/video_duplex/backend/settings.py`**

- 源码对模块职责的说明：Plugin-owned configuration persistence for the full-duplex application.。
- 调用入口 `settings_payload(enabled)`；声明返回 `dict[str, Any]`。
- 调用入口 `update_settings(values, clear_secrets)`；声明返回 `None`。
- 调用入口 `reply_language()`；声明返回 `str`。
- 调用入口 `set_enabled(enabled)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import os`；`from pathlib import Path`。
- 模块级配置或常量名称：`SETTING_ENV_KEYS`, `SECRET_SETTINGS`, `ALLOWED_REPLY_LANGUAGES`, `DEFAULTS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/settings.py#L1-L170)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/task_adapter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1616252b2d80a6d5ec70a805d2680a6f2190574b9246551e0d6ce531fadf6c81 -->
**`jiuwenswarm/extensions/video_duplex/backend/task_adapter.py`**

- 源码对模块职责的说明：Video RPC/presentation and Agent RPC adapters for the shared Host task service.。
- 调用入口 `task_identity(ws, scope)`。
- 异步入口 `task_agent_query(client, method, params, session, owner)`。
- `AgentTaskExecutor` 定义类型边界；方法入口：`__init__`, `close`, `run`, `wait_settled`, `answer_input`, `answer`。
- `VideoSearchManager` 定义类型边界；方法入口：`__init__`, `service`, `scope`, `authorized_scope`, `public`, `snapshot`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import asyncio`；`import json`；`import logging`；`import time`。
- 模块级配置或常量名称：`AGENT_QUERY_TIMEOUT`, `EVENT_SEND_TIMEOUT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/task_adapter.py#L1-L753)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/tasks/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=766d47c1dde313a77363f0b5d1f863f5a2bd022c66b6bf415d89dbe6ca4d8c86 -->
**`jiuwenswarm/extensions/video_duplex/backend/tasks/__init__.py`**

- 源码对模块职责的说明：Application task ownership; Agent execution remains in the existing runtime.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .service import TaskService`；`from .store import TaskStore`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/__init__.py#L1-L6)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/tasks/bridge.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4698d8e02ccba4a6e1ef8a2dae23f0851b830223f5073099219bc0dcac4f6e40 -->
**`jiuwenswarm/extensions/video_duplex/backend/tasks/bridge.py`**

- 源码对模块职责的说明：Gateway-owned checkpoint commands over the existing E2A push/ACK channel.。
- `GatewayTaskEndpoint` 定义类型边界；方法入口：`__init__`, `binding`, `close`, `execute`。
- `RemoteTaskEndpoint` 定义类型边界；方法入口：`__init__`, `call`。
- 调用入口 `resolve_checkpoint_ack(request)`。
- 异步入口 `handle_checkpoint_push(client, chunk, session_id)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import asyncio`；`import logging`；`import uuid`；`import weakref`。
- 模块级配置或常量名称：`EVENT`, `ACK_TIMEOUT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/bridge.py#L1-L168)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/tasks/checkpoint.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=430bd77eb45909bb3dfa45fd8bf4c51a22cba119c279b957d6359b8ed5ce80a8 -->
**`jiuwenswarm/extensions/video_duplex/backend/tasks/checkpoint.py`**

- 源码对模块职责的说明：Apply requirement changes to the exact root Agent model context.。
- `TaskCheckpoint` 定义类型边界；方法入口：`__init__`, `check`, `before_model`, `after_model`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/checkpoint.py#L1-L70)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/tasks/errors.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=88a91d0864adbe62666edae4e89b2f07d2567a689d09952a263b469e5f0cfd22 -->
**`jiuwenswarm/extensions/video_duplex/backend/tasks/errors.py`**

- 源码对模块职责的说明：Internal conflict types; human-readable wording is not a control protocol.。
- `QueueVersionConflict` 继承 `ValueError`。
- `TaskRevisionConflict` 继承 `ValueError`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/errors.py#L1-L9)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/tasks/execution.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f01e356a66c97fbb24d9b0441146b3ce34c8cac0c65322cd8a291e369fe76337 -->
**`jiuwenswarm/extensions/video_duplex/backend/tasks/execution.py`**

- 源码对模块职责的说明：Bind Host requests and output leases, and observe native execution settlement.。
- `TaskExecutionBinding` 继承 `TaskCheckpoint`；方法入口：`__init__`, `capture_execution`。
- 异步入口 `bind_task_execution(request, adapter, inputs)`。
- 异步入口 `bind_task_output(rail, request, stream)`。
- 异步入口 `close_task_output(rail, request)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import asyncio`；`from contextlib import asynccontextmanager`；`import logging`；`from .checkpoint import TaskCheckpoint`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/execution.py#L1-L152)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/tasks/interactions.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c04bb6a0eb314adfdca567b7f843bbec0b41b11999e6b21bc7898c9c6c8f2cf9 -->
**`jiuwenswarm/extensions/video_duplex/backend/tasks/interactions.py`**

- 源码对模块职责的说明：Validate observed information questions without granting approval authority.。
- 调用入口 `information_question(payload)`。
- 调用入口 `native_approval_question(payload)`。
- 调用入口 `validate_native_approval_answers(interaction, answers)`。
- 调用入口 `validate_answers(interaction, answers)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from copy import deepcopy`。
- 模块级配置或常量名称：`NATIVE_APPROVAL_SOURCES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/interactions.py#L1-L108)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/tasks/prompts.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8f5285fcfeee96c2a7d0e712f858962d655dcddba1c75401f5e1ac0e858c9415 -->
**`jiuwenswarm/extensions/video_duplex/backend/tasks/prompts.py`**

- 源码对模块职责的说明：Model-facing task instructions. User requirements and results are opaque data.。
- 调用入口 `task_query_instructions(total, counts, unfinished, page_size, matched)`。
- 调用入口 `task_receipt_followup(receipt)`。
- 调用入口 `build_execution_prompt(question, query, visual_context, context_text, brief_protocol)`。
- 调用入口 `build_brief_prompt(begin, end, language_rule)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import json`。
- 模块级配置或常量名称：`JOYAI_TASK_INSTRUCTIONS`, `EMPTY_QUERY_INSTRUCTIONS`, `REORDER_INSTRUCTIONS`, `QUEUE_CONFLICT_INSTRUCTIONS`, `REVISION_CONFLICT_INSTRUCTIONS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/prompts.py#L1-L104)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/video_files.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ece0fd8e294a170991ae5354c6b12eac23b70b98fea88418e81b5d99c6223f39 -->
**`jiuwenswarm/extensions/video_duplex/backend/video_files.py`**

- 源码对模块职责的说明：Preserve native Jiuwen file resources across the duplex event bridge.。
- 调用入口 `normalize_file_items(value)`；声明返回 `list[dict[str, Any]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/video_files.py#L1-L23)。
<!-- /kb:file -->
