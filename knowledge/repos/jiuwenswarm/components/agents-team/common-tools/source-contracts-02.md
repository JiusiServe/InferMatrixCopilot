---
title: "common-tools 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-tools 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/mcp_toolkits.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=43a55b08cf0730df863f1f9e5f8c32b39e319fe18d21de2217bbb92a4c2decf1 -->
**`jiuwenswarm/agents/harness/common/tools/mcp_toolkits.py`**

- 源码对模块职责的说明：MCP toolkit aggregator for openjiuwen tools.。
- 调用入口 `track_mcp_search_tools(ability_manager)`；声明返回 `None`。
- 调用入口 `refresh_mcp_paid_search_tools()`；声明返回 `None`。
- 调用入口 `get_mcp_tools()`；声明返回 `list[Tool]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`from weakref import WeakSet`；`from openjiuwen.core.foundation.tool import Tool`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/mcp_toolkits.py#L1-L81)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/memory_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=957fe0cdec925b360469f1c0ebacdfd931a18a495715a00033f995888f6d49d9 -->
**`jiuwenswarm/agents/harness/common/tools/memory_tools.py`**

- 源码对模块职责的说明：Memory tools for JiuWenSwarm - Using @tool decorator for openjiuwen.。
- 调用入口 `set_group_chat_mode(enabled)`；声明返回 `contextvars.Token`。
- 调用入口 `is_group_chat_mode()`；声明返回 `bool`。
- 调用入口 `set_global_memory_manager(manager, workspace_dir, settings, agent_id)`。
- 异步入口 `init_memory_manager_async(workspace_dir, agent_id)`；声明返回 `Optional[MemoryIndexManager]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import contextvars`；`import logging`；`import os`；`import re`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/memory_tools.py#L1-L536)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/multi_session_toolkits.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a68976e9e263677d01035e16fd544d70e55b191a4e8169e0fbf55dca5ce83adb -->
**`jiuwenswarm/agents/harness/common/tools/multi_session_toolkits.py`**

- 源码对模块职责的说明：Session Toolkit 生命周期：Agent创建新session开始，到所有session协程结束。
- `Status` 继承 `str, Enum`。
- `SessionTask` 继承 `BaseModel`。
- `MultiSessionToolkit` 定义类型边界；方法入口：`__init__`, `get_sub_agent`, `notify`, `create_new_sessions`, `cancel_session`, `list_all_sessions`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/multi_session_toolkits.py#L1-L508)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/pdf_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3951680e62666aa2819c56e7a7d300968e733630eaaf4362ad655637507b2824 -->
**`jiuwenswarm/agents/harness/common/tools/pdf_tools.py`**

- 源码对模块职责的说明：Page-level PDF reading tool.。
- `ReadPdfRequest` 定义类型边界。
- 异步入口 `read_pdf(pdf_path, pages, max_chars, **kwargs)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from dataclasses import dataclass`。
- 模块级配置或常量名称：`DEFAULT_MAX_CHARS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/pdf_tools.py#L1-L275)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/search_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0b46d727eb870b2d85460a365d1c555b5cca13606e66a5ee5da092317586325c -->
**`jiuwenswarm/agents/harness/common/tools/search_tools.py`**

- 源码对模块职责的说明：Neutral structured search providers and result renderers.。
- 调用入口 `normalize_search_max_results(value)`；声明返回 `int`。
- 调用入口 `run_free_search_structured(query, max_results, timeout_seconds)`；声明返回 `tuple[str, list[dict[str, str]]]`。
- 调用入口 `render_free_search_result(query, engine_used, rows)`；声明返回 `str`。
- 调用入口 `configured_paid_search_providers()`；声明返回 `list[str]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import base64`；`import os`。
- 模块级配置或常量名称：`DEFAULT_SEARCH_MAX_RESULTS`, `MIN_SEARCH_MAX_RESULTS`, `MAX_SEARCH_MAX_RESULTS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/search_tools.py#L1-L610)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/send_file_to_user.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=00e3f27cd067dfe9f0b4a8da5ff7ff5662ac46e0e489b02bf0fa3113f8327bd3 -->
**`jiuwenswarm/agents/harness/common/tools/send_file_to_user.py`**

- 源码对模块职责的说明：Send File Toolkit。
- 调用入口 `looks_like_skill_package(path)`；声明返回 `bool`。
- 调用入口 `clear_sent_files_for_session(session_id)`；声明返回 `None`。
- `SendFileToolkit` 定义类型边界；方法入口：`__init__`, `update_runtime_context`, `send_file`, `get_tools`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import copy`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/send_file_to_user.py#L1-L832)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fac5c30fee8a5015123380a9561066b4644540e1174160d0abd2eb118c258bcb -->
**`jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py`**

- 源码对模块职责的说明：Agent tools for discovering and messaging other product Sessions.。
- `SessionMessagingRoute` 定义类型边界；方法入口：`source_for_call`, `source_for_list`, `to_wire`。
- 调用入口 `bind_session_messaging_route(session_id, request_id, user_id, cross_session)`；声明返回 `Token[SessionMessagingRoute / None]`。
- 调用入口 `reset_session_messaging_route(token)`；声明返回 `None`。
- 调用入口 `current_session_messaging_route()`；声明返回 `SessionMessagingRoute / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import json`；`import logging`。
- 模块级配置或常量名称：`SESSION_MESSAGING_ROUTE_EXTRA_KEY`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/session_messaging_toolkit.py#L1-L613)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/skill_retrieval_toolkits.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=43fe5ed187f267409ca8c87f1e319f984e7d0ea5baf421eec2f4036b6e0a4d79 -->
**`jiuwenswarm/agents/harness/common/tools/skill_retrieval_toolkits.py`**

- 源码对模块职责的说明：JiuwenSwarm adaptation for Symphony's DCI-compatible Skill discovery.。
- 调用入口 `is_valid_skill_retrieval_session_profile(profile)`；声明返回 `bool`。
- 调用入口 `skill_sources_from_manager(manager)`；声明返回 `dict[str, str]`。
- 调用入口 `is_skill_retrieval_enabled(config_base)`；声明返回 `bool`。
- 调用入口 `is_skill_retrieval_index_enabled(config_base)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import logging`；`from collections.abc import Callable, Iterable, Mapping, Sequence`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/skill_retrieval_toolkits.py#L1-L651)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/skill_toolkits.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a356df0ca3773a0a5d8d104c19b87a43500de4f04352bbff38299c84e0835834 -->
**`jiuwenswarm/agents/harness/common/tools/skill_toolkits.py`**

- 源码对模块职责的说明：面向 agent 的 skill 管理工具封装。。
- `SkillToolkit` 定义类型边界；方法入口：`__init__`, `search_skill`, `install_skill`, `uninstall_skill`, `get_tools`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import hashlib`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/skill_toolkits.py#L1-L902)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/ssl_config.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a2f8ce0e1881d39488bf2c32b250667acee11fe4d1b532063f66f2b3b4b598a6 -->
**`jiuwenswarm/agents/harness/common/tools/ssl_config.py`**

- 源码对模块职责的说明：Shared SSL verification configuration for HTTP tools.。
- 调用入口 `get_ssl_verify()`；声明返回 `bool`。
- 调用入口 `get_requests_verify()`；声明返回 `bool`。
- 调用入口 `get_insecure_ssl_context()`；声明返回 `ssl.SSLContext`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import ssl`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/ssl_config.py#L1-L35)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/symphony_toolkits.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4fa2ae3f4d7735ae0d7f5fc54d6326968705ab2c140aa8bb7ebb0ad3b2397792 -->
**`jiuwenswarm/agents/harness/common/tools/symphony_toolkits.py`**

- 源码对模块职责的说明：Agent-facing Symphony tools.。
- `SymphonyToolkit` 定义类型边界；方法入口：`__init__`, `graph_status`, `refresh_graph`, `plan`, `is_enabled`, `get_tools`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/symphony_toolkits.py#L1-L454)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/todo_compat.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8af737a0d2f6ffcb9bb7cc42cd5e69f31d75c3612af8b0a32a47ee0653472cd0 -->
**`jiuwenswarm/agents/harness/common/tools/todo_compat.py`**

- 源码对模块职责的说明：Compatibility shims for OpenJiuWen todo tools.。
- `CompatibleTodoModifyTool` 继承 `_OpenJiuWenTodoModifyTool`。
- 调用入口 `install_todo_modify_compat_patch()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from openjiuwen.core.common.exception.codes import StatusCode`；`from openjiuwen.core.common.exception.errors import build_error`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/todo_compat.py#L1-L94)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/todo_toolkits.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a6dbbcb2dc5d69fd37edeac5aeac2fa3eb170baae0c6d925e9ec9749cbbce36f -->
**`jiuwenswarm/agents/harness/common/tools/todo_toolkits.py`**

- 源码对模块职责的说明：Todo toolkit for agent task tracking.。
- `TaskStatus` 继承 `str, Enum`。
- `TodoTask` 继承 `BaseModel`。
- `TodoToolkit` 定义类型边界；方法入口：`__init__`, `todo_create`, `todo_complete`, `todo_insert`, `todo_remove`, `todo_list`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import threading`；`from enum import Enum`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/todo_toolkits.py#L1-L367)。
<!-- /kb:file -->
