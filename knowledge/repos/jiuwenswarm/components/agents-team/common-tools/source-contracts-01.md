---
title: "common-tools 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-tools 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d52ab393e4e7f0226ef59d0913054dbb2eedea24c8dd9701b6010e02b594d0bd -->
**`jiuwenswarm/agents/harness/common/tools/__init__.py`**

- 源码对模块职责的说明：Tools for JiuWenSwarm AgentServer.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .memory_tools import set_global_memory_manager, init_memory_manager_as`；`from .send_file_to_user import SendFileToolkit`；`from .skill_toolkits import SkillToolkit`；`from .skill_retrieval_toolkits import build_model_discovery_settings, is_sk`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/__init__.py#L1-L82)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/acp_chat/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aa8781e57a6b3ca44987b913dcc04c1ac5cb02e03960dd013be69ff8f738e1c0 -->
**`jiuwenswarm/agents/harness/common/tools/acp_chat/__init__.py`**

- 源码对模块职责的说明：External ACP agent chat tool (stdio subprocess).。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.agents.harness.common.tools.acp_chat.tool import acp_chat`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/acp_chat/__init__.py#L1-L7)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/acp_chat/tool.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4473206e3bd9157b6ede7c6a4d298311297dbe1cdafcd766904b9cccaf44fbd8 -->
**`jiuwenswarm/agents/harness/common/tools/acp_chat/tool.py`**

- 源码对模块职责的说明：Tool: forward a prompt to an external ACP agent (stdio) configured in config.yaml.。
- 异步入口 `acp_chat(agent, message, new_session)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/acp_chat/tool.py#L1-L124)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/acp_output_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=caaef88512654d4a43c38cf8eae8bde81b867e3f656d241416bc1c00b003bf99 -->
**`jiuwenswarm/agents/harness/common/tools/acp_output_tools.py`**

- 源码对模块职责的说明：ACP 输出工具：AgentServer 向 IDE 发送请求。。
- `AcpOutputRequest` 定义类型边界。
- `AcpOutputManager` 定义类型边界；方法入口：`__init__`, `set_send_push_callback`, `reset_state`, `add_pending_request`, `complete_jsonrpc_response`, `fail_jsonrpc_response`。
- 调用入口 `get_acp_output_manager()`；声明返回 `AcpOutputManager`。
- `AcpOutputError` 继承 `Exception`；方法入口：`__init__`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import inspect`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/acp_output_tools.py#L1-L585)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/audio_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c8d615e1e96e340d3ae63c39ba63a0987984d3eb7a666ad5b35d76898fbc2b30 -->
**`jiuwenswarm/agents/harness/common/tools/audio_tools.py`**

- 异步入口 `audio_question_answering(audio_path_or_url, question)`；声明返回 `str`。
- 异步入口 `audio_metadata(audio_path_or_url)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import base64`；`import contextlib`；`import hashlib`；`import hmac`。
- 模块级配置或常量名称：`ACR_ACCESS_KEY`, `ACR_ACCESS_SECRET`, `ACR_BASE_URL`, `HTTP_TIMEOUT`, `MAX_AUDIO_BYTES`, `DEFAULT_USER_AGENT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/audio_tools.py#L1-L329)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/bash_tool_safety.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1fb94aafd00ce891c247d88e93bdedbce3f44096e488a39588893c6b641ea436 -->
**`jiuwenswarm/agents/harness/common/tools/bash_tool_safety.py`**

- 源码对模块职责的说明：Apply jiuwenswarm shell safety rules to openjiuwen BashTool / PowerShellTool.。
- 调用入口 `install_shell_tool_safety_hooks()`；声明返回 `None`。
- 调用入口 `reset_installed_flag()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import contextlib`；`import os`；`from typing import Any, Awaitable, Callable`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/bash_tool_safety.py#L1-L186)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/browser_timeout_policy.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2a1d2571a57b2aa2cd6c8217748bbe16be9b661a523ebcb88b4f569353cea547 -->
**`jiuwenswarm/agents/harness/common/tools/browser_timeout_policy.py`**

- 源码对模块职责的说明：Timeout policy helpers for browser runtime calls.。
- 调用入口 `allow_short_timeout_override()`；声明返回 `bool`。
- 调用入口 `resolve_browser_task_timeout(requested_timeout_s, default_timeout_s)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`from typing import Optional`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/browser_timeout_policy.py#L1-L36)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/command_execution_context.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eef36cb7263549e21fb1ae6364cb4508c2d3eb863895a954faf0d5c5c6f4c3d1 -->
**`jiuwenswarm/agents/harness/common/tools/command_execution_context.py`**

- 源码对模块职责的说明：Request-local command execution ownership.。
- `CommandExecutionBinding` 定义类型边界。
- 调用入口 `bind_command_execution(sys_operation, sandboxed)`；声明返回 `Token[CommandExecutionBinding / None]`。
- 调用入口 `bind_no_command_execution()`；声明返回 `Token[CommandExecutionBinding / None]`。
- 调用入口 `current_command_execution()`；声明返回 `CommandExecutionBinding / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from contextvars import ContextVar, Token`；`from dataclasses import dataclass`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_execution_context.py#L1-L60)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/command_runtime.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4e52b41e028c297a7b6474ced9fdd1a0e33e5252aed765da8192b02d9ed07445 -->
**`jiuwenswarm/agents/harness/common/tools/command_runtime.py`**

- 源码对模块职责的说明：Shared runtime contract for command working directories.。
- `CommandRuntimePaths` 定义类型边界。
- 调用入口 `current_command_runtime_paths(require_runtime_cwd)`；声明返回 `CommandRuntimePaths`。
- 调用入口 `resolve_command_workdir(workdir, runtime_paths)`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from pathlib import Path`；`from jiuwenswarm.common.utils import get_agent_workspace_dir`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_runtime.py#L1-L98)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/command_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f5f2f0801ae54b0931c7a06fb18395596c27d048b61f47312cedaeed1fbbfe8a -->
**`jiuwenswarm/agents/harness/common/tools/command_tools.py`**

- 源码对模块职责的说明：Command execution tools implemented with openjiuwen @tool style.。
- `CommandCancelled` 继承 `Exception`。
- 异步入口 `mcp_exec_command(command, timeout_seconds, workdir, max_output_chars, shell_type, background)`；声明返回 `str`。
- 调用入口 `reset_tui_spawn_history()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import contextlib`；`import json`。
- 模块级配置或常量名称：`TUI_SPAWN_LIMIT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_tools.py#L1-L1223)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/cron/cron_runtime.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e5695e7695fcbd7e38a3afa7339153fc407cc4e4990b26b9998d18aadfa9db79 -->
**`jiuwenswarm/agents/harness/common/tools/cron/cron_runtime.py`**

- `CronRuntimeBridge` 定义类型边界；方法入口：`__init__`, `set_backend`, `get_backend`, `ensure_scheduler_started`, `build_tools`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import re`；`import time`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/cron/cron_runtime.py#L1-L1075)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/cron/cron_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9612aea3181021a011e7e2155b2d1f0dbe70923137679692a3b2970b85df39dd -->
**`jiuwenswarm/agents/harness/common/tools/cron/cron_tools.py`**

- 调用入口 `install_gateway_jobs_snapshot(rows, user_id)`；声明返回 `int`。
- 调用入口 `resolve_gateway_cron_command_ack(command_id, result)`；声明返回 `None`。
- 调用入口 `register_gateway_run_ack(request_id)`；声明返回 `asyncio.Future[str] / None`。
- 调用入口 `resolve_gateway_run_ack(request_id, run_id)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import contextvars`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/cron/cron_tools.py#L1-L1085)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/file_delivery_policy.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=54b01b7f8716462ae80bbdde1ae31747b184038f808feb6f80cabd4e26a89f2f -->
**`jiuwenswarm/agents/harness/common/tools/file_delivery_policy.py`**

- 源码对模块职责的说明：File delivery capability for public channels and their internal delegates.。
- 调用入口 `is_send_file_enabled(config, channel_id)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/file_delivery_policy.py#L1-L12)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/tools/gen_toolkits.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=446ec968ca46a9b6bb74e53aa0fa86e524a2264cb9e908215e4485848946809e -->
**`jiuwenswarm/agents/harness/common/tools/gen_toolkits.py`**

- 源码对模块职责的说明：Vendor-native image / video generation backends (MiniMax, BytePlus ModelArk).。
- `GenerationTarget` 定义类型边界。
- `VideoRequest` 定义类型边界。
- 调用入口 `detect_backend(protocol_env, api_base)`；声明返回 `str / None`。
- 异步入口 `generate_image(target, prompt, aspect_ratio, save_dir)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import base64`；`import logging`。
- 模块级配置或常量名称：`MINIMAX`, `MODELARK`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/gen_toolkits.py#L1-L727)。
<!-- /kb:file -->
