---
title: "server-runtime 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# server-runtime 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=21a07688703b649808ec7986378208a753d738725cd7a3b110d089616897047c -->
**`jiuwenswarm/server/runtime/a2ui/__init__.py`**

- 源码对模块职责的说明：A2UI feature package.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.runtime.a2ui.config import A2UIConfig, get_a2ui_con`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/__init__.py#L1-L16)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/config.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7b08292d88482f10c491e05f606c9cd6b14ca1543911cb80998e0d208d9f95c5 -->
**`jiuwenswarm/server/runtime/a2ui/config.py`**

- 源码对模块职责的说明：Configuration helpers for the A2UI feature.。
- 调用入口 `get_current_a2ui_config()`；声明返回 `A2UIConfig`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.server.control.a2ui_config import A2UIConfig, SUPPORTED_A2`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/config.py#L1-L31)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/integration.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5e6a272e6901ec05105e2adebba7526ed8d6de91b28b7668fea8b61f092b69b2 -->
**`jiuwenswarm/server/runtime/a2ui/integration.py`**

- 源码对模块职责的说明：Integration helpers for wiring A2UI into jiuwenswarm host modules.。
- 调用入口 `is_a2ui_channel(channel)`；声明返回 `bool`。
- 调用入口 `build_user_prompt_if_a2ui_event(content, channel, language)`；声明返回 `str / None`。
- 异步入口 `finalize_assistant_response_if_a2ui(content, channel, user_query, request_id, repair_call, retry_without_a2ui_call)`；声明返回 `str`。
- 调用入口 `apply_non_web_text_fallback_to_payload(payload, channel_id)`；声明返回 `dict[str, object]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Any`；`from jiuwenswarm.server.runtime.a2ui.config import get_a2ui_config, get_cur`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/integration.py#L1-L167)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/parser.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1bbeec7bd9537efecb8d0ec7fe5774abb882069090101e883835c32c66eb9063 -->
**`jiuwenswarm/server/runtime/a2ui/parser.py`**

- 源码对模块职责的说明：A2UI response parsing helpers.。
- 调用入口 `is_a2ui_message(value)`；声明返回 `bool`。
- 调用入口 `coerce_message_list(value)`；声明返回 `list[dict[str, Any]] / None`。
- 调用入口 `iter_tagged_block_bodies(text)`；声明返回 `list[tuple[int, str]]`。
- 调用入口 `strip_tagged_a2ui_blocks(text)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import copy`；`import json`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/parser.py#L1-L129)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/prompt_instructions.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b799f121d0f8658af96cfd22b204f9036d72a38dd769cde267adbdf8b0bdbe83 -->
**`jiuwenswarm/server/runtime/a2ui/prompt_instructions.py`**

- 源码对模块职责的说明：Request-scoped A2UI prompt rail instructions.。
- 调用入口 `is_a2ui_browser_workflow_request(value)`；声明返回 `bool`。
- 调用入口 `build_a2ui_browser_workflow_instruction()`；声明返回 `str`。
- 调用入口 `build_a2ui_autonomy_instruction(language)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import re`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/prompt_instructions.py#L1-L327)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/protocol.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=65b780c2390db70ecddafe282e31e287493fa4f7adaebfda66d8e192b09dbc2c -->
**`jiuwenswarm/server/runtime/a2ui/protocol.py`**

- 源码对模块职责的说明：A2UI v0.8 protocol adapter and public protocol facade.。
- `A2UIProtocolSpec` 定义类型边界；方法入口：`__init__`, `catalog`, `build_prompt`, `load_examples`, `render_examples`, `parse_response`。
- 调用入口 `get_protocol_spec(version)`；声明返回 `A2UIProtocolSpec`。
- 调用入口 `build_a2ui_prompt_section(language, include_browser_workflows)`；声明返回 `str`。
- 调用入口 `format_a2ui_for_text_channel(content, version)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`from functools import lru_cache`。
- 模块级配置或常量名称：`A2UI_ACTIVE_PROTOCOL_VERSION`, `A2UI_CLIENT_EVENT_TYPE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/protocol.py#L1-L761)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/protocols/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5a231a50ce2b78dd8c18b966ac3bcab9d6cf89fac8158c14c82f7c4f891a309b -->
**`jiuwenswarm/server/runtime/a2ui/protocols/__init__.py`**

- 源码对模块职责的说明：Versioned A2UI protocol registry exports.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.runtime.a2ui.protocol import A2UIProtocolSpec, get_`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/protocols/__init__.py#L1-L10)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/runtime/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7b507e6eb1e4c2de61b91733f9a19629ce4fd3026b544b66531886965ff0f166 -->
**`jiuwenswarm/server/runtime/a2ui/runtime/__init__.py`**

- 源码对模块职责的说明：Runtime helpers for A2UI request handling.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.runtime.a2ui.protocol import A2UIStreamGuard, build`；`from jiuwenswarm.server.runtime.a2ui.runtime.response_finalization import f`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/runtime/__init__.py#L1-L23)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/runtime/formatter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=286ff69faaa759b54c3c7d0b89349f6f3750fe3a9737f48eb0c8a74cf1c2148c -->
**`jiuwenswarm/server/runtime/a2ui/runtime/formatter.py`**

- 源码对模块职责的说明：Legacy A2UI text formatting helpers kept for compatibility.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.runtime.a2ui.protocol import format_a2ui_for_text_c`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/runtime/formatter.py#L1-L10)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/runtime/prompt.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5c0100cebc772a0311676ec39c74ce6234c9afa3d42764faf81fb5b9303cb884 -->
**`jiuwenswarm/server/runtime/a2ui/runtime/prompt.py`**

- 源码对模块职责的说明：A2UI prompt builders.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.runtime.a2ui.protocol import build_a2ui_client_even`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/runtime/prompt.py#L1-L13)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=98576ae776622be8a5e9d2a8524cda58079cb26515a623bb04b445e4a3fc0457 -->
**`jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py`**

- 源码对模块职责的说明：Runtime helpers for validating and repairing assistant A2UI responses.。
- 异步入口 `finalize_a2ui_assistant_content(content, user_query, request_id, repair_call, a2ui_enabled, retry_without_a2ui_call)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/runtime/response_finalization.py#L1-L205)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/runtime/stream.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9f2a488becd5312064b8223da99774c3c45e48bf8b93dfa6bbd7f40de688caeb -->
**`jiuwenswarm/server/runtime/a2ui/runtime/stream.py`**

- 源码对模块职责的说明：A2UI streaming output guard.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.runtime.a2ui.protocol import A2UIStreamGuard`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/runtime/stream.py#L1-L7)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/runtime/team_stream.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=97fb7a09f89d7922877a86b5498a3ad851ad260a9848f048b6d1c87822fa10f0 -->
**`jiuwenswarm/server/runtime/a2ui/runtime/team_stream.py`**

- 源码对模块职责的说明：Member-scoped A2UI buffering for persistent Team streams.。
- `TeamA2UIBlockDecision` 定义类型边界。
- `TeamA2UIBlockBuffer` 定义类型边界；方法入口：`__init__`, `key_for`, `remember_finalized`, `consume`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass, field`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/runtime/team_stream.py#L1-L193)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/stream_guard.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=afa87801beb84e6133dc43cb7c2655a5f60322b3fc5921c416cbc6585c6583ab -->
**`jiuwenswarm/server/runtime/a2ui/stream_guard.py`**

- 源码对模块职责的说明：Streaming guard for tagged A2UI blocks.。
- `A2UIStreamGuard` 定义类型边界；方法入口：`__init__`, `feed`, `finish`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from a2ui.schema.constants import A2UI_CLOSE_TAG, A2UI_OPEN_TAG`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/stream_guard.py#L1-L78)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/support.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=03541f53dc1ec8e31480d1295f758142e9c044058da59ce1ff6e93172744b5f9 -->
**`jiuwenswarm/server/runtime/a2ui/support.py`**

- 源码对模块职责的说明：Compatibility facade for the modular A2UI feature package.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.runtime.a2ui.prompt_instructions import build_a2ui_`；`from jiuwenswarm.server.runtime.a2ui.protocol import A2UI_ACTIVE_PROTOCOL_V`；`from jiuwenswarm.server.runtime.a2ui.types import A2UIExample, A2UIResponse`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/support.py#L1-L48)。
<!-- /kb:file -->
