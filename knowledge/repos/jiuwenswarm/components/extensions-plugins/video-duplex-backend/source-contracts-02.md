---
title: "video-duplex-backend 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# video-duplex-backend 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/tasks/server_adapter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=83f9097ed081bcf115ad4fdb834574c8fed553b7511d873f0f7d448dbe7c0ae7 -->
**`jiuwenswarm/extensions/video_duplex/backend/tasks/server_adapter.py`**

- 源码对模块职责的说明：AgentServer endpoints for checkpoint ACKs and task-produced files.。
- `VoiceTaskServerAdapter` 继承 `GatewayAdapter`；方法入口：`handle`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import asyncio`；`import re`；`from jiuwenswarm.common.schema.agent import AgentResponse`；`from jiuwenswarm.common.schema.message import ReqMethod`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/server_adapter.py#L1-L52)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/tasks/service.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f7c1cc48c1b0809727832f64ce53b657d5502236d4ccc3c564b5f086b34b436 -->
**`jiuwenswarm/extensions/video_duplex/backend/tasks/service.py`**

- 源码对模块职责的说明：Durable user tasks over an injected Agent executor, independent of media/RPC.。
- `TaskModification` 定义类型边界。
- `ExecutionUncertain` 继承 `RuntimeError`。
- `InteractionPending` 继承 `RuntimeError`。
- `TaskService` 定义类型边界；方法入口：`__init__`, `start`, `kick`, `submit`, `get`, `list`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import asyncio`；`import hashlib`；`import json`；`import logging`。
- 模块级配置或常量名称：`TERMINAL`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/service.py#L1-L798)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/tasks/store.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eef35d76b4b4804e6a977f8ebf44e0b4f5c979bc174ebcf9efa4ac94636e9232 -->
**`jiuwenswarm/extensions/video_duplex/backend/tasks/store.py`**

- 源码对模块职责的说明：One SQLite record of task facts and idempotent user operations.。
- 调用入口 `task_database()`。
- 调用入口 `encode(value)`。
- `TaskStore` 定义类型边界；方法入口：`__init__`, `transaction`, `get`, `put`, `rows`, `replay`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from contextlib import contextmanager`；`import hashlib`；`import json`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/tasks/store.py#L1-L124)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/video_live.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d132154fc069ab754d5ec8fb018fd742f2499bcdc5349ef82c34feb731d48769 -->
**`jiuwenswarm/extensions/video_duplex/backend/video_live.py`**

- 源码对模块职责的说明：Jiuwen Web RPC for short-window realtime audio-video Q&A.。
- 调用入口 `video_duplex_enabled()`；声明返回 `bool`。
- 调用入口 `register_video_live_handler(channel, agent_client, normalize_media_attachments)`；声明返回 `video_search.VideoSearchManager`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`from datetime import datetime, timezone`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/video_live.py#L1-L698)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/video_search.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4eb35864ae080cf5ef001905e4594d99445346bd338dbffc4080aa10abb6f7fe -->
**`jiuwenswarm/extensions/video_duplex/backend/video_search.py`**

- 源码对模块职责的说明：Core Agent execution and asynchronous search jobs for video-live sessions.。
- 调用入口 `core_agent_brief_protocol(nonce)`；声明返回 `str`。
- 调用入口 `present_core_agent_result(raw_answer, nonce, question, tools_used)`；声明返回 `dict[str, Any]`。
- 调用入口 `core_agent_text(value, limit)`；声明返回 `str`。
- 调用入口 `core_agent_progress(payload)`；声明返回 `dict[str, Any] / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import re`。
- 模块级配置或常量名称：`VIDEO_TOOL_CHANNEL_ID`, `MAX_FRAME_CHARS`, `MAX_DELEGATION_CONTEXT_ITEMS`, `MAX_DELEGATION_CONTEXT_CHARS`, `MAX_DELEGATION_RESULT_CHARS`, `MAX_REALTIME_BRIEF_CHARS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/video_search.py#L1-L539)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/video_duplex/backend/video_voice.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a3ec3acec41f0b444622ec4aa6e5b3e25c11dc1f70185870a8ef18aa6f1e2024 -->
**`jiuwenswarm/extensions/video_duplex/backend/video_voice.py`**

- 源码对模块职责的说明：ASR and TTS adapters shared by video-live providers.。
- 调用入口 `is_allowed_audio_data_url(value)`；声明返回 `bool`。
- 调用入口 `tts_model_config()`；声明返回 `tuple[str, str, str, str]`。
- 调用入口 `asr_model_config()`；声明返回 `tuple[str, str, str]`。
- 调用入口 `clean_model_text(text)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import base64`；`import os`。
- 模块级配置或常量名称：`MAX_AUDIO_CHARS`, `MAX_TTS_TEXT_CHARS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/video_duplex/backend/video_voice.py#L1-L558)。
<!-- /kb:file -->
