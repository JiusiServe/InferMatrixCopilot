---
title: "common 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/electron_sideview.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a97a788b4f4b512a34364a173d494fce6b625cc9b4e2e9acc70b0387b35f3249 -->
**`jiuwenswarm/agents/harness/common/electron_sideview.py`**

- 源码对模块职责的说明：Opt-in Electron binding: independent pages, shared persistent login state.。
- 调用入口 `electron_target_resolver_base()`；声明返回 `str`。
- 调用入口 `electron_browser_selected()`；声明返回 `bool`。
- 调用入口 `electron_discovery_file_path()`；声明返回 `Path`。
- 调用入口 `load_electron_browser_endpoints(max_age_s)`；声明返回 `dict[str, Any] / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import json`；`import os`。
- 模块级配置或常量名称：`DISCOVERY_FILE_NAME`, `DISCOVERY_MAX_AGE_S`, `FORCE_MANAGED_ENV`, `DISCOVERY_OPT_IN_ENV`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/electron_sideview.py#L1-L249)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/memory_rpc.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e065b095ed672a65ffb99ed51f12bbcc4c5956e916af053e144aa0cdb043b673 -->
**`jiuwenswarm/agents/harness/common/memory_rpc.py`**

- 异步入口 `handle_memory_list(workspace, mode, params)`；声明返回 `dict[str, Any]`。
- 异步入口 `handle_memory_edit(workspace, params)`；声明返回 `dict[str, Any]`。
- 异步入口 `handle_memory_status(workspace, mode, params)`；声明返回 `dict[str, Any]`。
- 异步入口 `handle_memory_toggle(workspace, mode, params)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import os`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory_rpc.py#L1-L624)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/session_ops_service.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1a45eb7be0540e4b8b1a2e40d295cdf12068d87004d1f39dd83d0dd89d7b2d35 -->
**`jiuwenswarm/agents/harness/common/session_ops_service.py`**

- 调用入口 `fork_session(source_session_id, target_session_id, title, channel_id, cutoff_message_id, cutoff_role, cutoff_content, cutoff_timestamp, session_equipment_override)`；声明返回 `dict[str, Any]`。
- 调用入口 `rewind_session(session_id, turn_index)`；声明返回 `dict[str, Any]`。
- 调用入口 `compact_partial_session(session_id, turn_index, direction, llm_summary)`；声明返回 `dict[str, Any]`。
- 调用入口 `list_session_turns(session_id, project_dir)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import copy`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/session_ops_service.py#L1-L1984)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tool_progress_context.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d84c7e07b80eda0097463c1203c41a280546df4fd08f530e68ee85a0ca1b2ce5 -->
**`jiuwenswarm/agents/harness/common/tool_progress_context.py`**

- 源码对模块职责的说明：Task-local progress callback for long-running agent tools.。
- 调用入口 `bind_tool_progress(callback)`；声明返回 `Token`。
- 调用入口 `current_tool_progress()`；声明返回 `ToolProgressCallback / None`。
- 调用入口 `reset_tool_progress(token)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from contextvars import ContextVar, Token`；`from typing import Any, Awaitable, Callable`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tool_progress_context.py#L1-L26)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/workspace_paths.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c50a58ac2dc4ed0ac4b397e5ba1c815eafa25f0a21934ebb3842008bfe112da3 -->
**`jiuwenswarm/agents/harness/common/workspace_paths.py`**

- 源码对模块职责的说明：Shared workspace path resolution and display sanitization helpers.。
- `WorkspacePathResolution` 定义类型边界。
- 调用入口 `normalize_workspace_root(workspace_root)`；声明返回 `Path / None`。
- 调用入口 `sandbox_artifact_session_root(path)`；声明返回 `Path / None`。
- 调用入口 `is_sandbox_artifact_workspace_root(path)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import re`；`import unicodedata`；`from collections.abc import Mapping`。
- 模块级配置或常量名称：`WORKSPACE_CURRENT_URI`, `WORKSPACE_CURRENT_URI_PREFIX`, `STALE_SANDBOX_ARTIFACT_PATH`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/workspace_paths.py#L1-L515)。
<!-- /kb:file -->
