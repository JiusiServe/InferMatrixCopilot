---
title: "common-rails 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-rails 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c91811ffeb7c45f731cfc861c4f6cc335fd654d71fccb67c8f31a77670c6598e -->
**`jiuwenswarm/agents/harness/common/rails/__init__.py`**

- 源码对模块职责的说明：JiuWenSwarm Rails for DeepAgent integration.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from openjiuwen.harness.rails.security import PermissionInterruptRail`；`from jiuwenswarm.agents.harness.common.rails.avatar_rail import AvatarPromp`；`from jiuwenswarm.agents.harness.common.rails.browser_task_prompt_rail impor`；`from jiuwenswarm.agents.harness.common.rails.project_memory_rail import Pro`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/__init__.py#L1-L38)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/ask_user_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3fba605833bc91da10824825074799040d95f2c1181683a3763224d835907ce9 -->
**`jiuwenswarm/agents/harness/common/rails/ask_user_rail.py`**

- 源码对模块职责的说明：Extended AskUserRail that supports structured questions with options.。
- `StructuredAskUserPayload` 继承 `BaseModel`。
- `StructuredAskUserTool` 继承 `Tool`；方法入口：`__init__`, `invoke`, `stream`。
- `StructuredAskUserRail` 继承 `AskUserRail`；方法入口：`__init__`, `set_strict_continuation_contract`, `init`, `uninit`, `get_structured_tools`, `resolve_interrupt`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import uuid`。
- 模块级配置或常量名称：`EXTENDED_INPUT_PARAMS_EN`, `EXTENDED_INPUT_PARAMS_CN`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/ask_user_rail.py#L1-L597)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/browser_task_prompt_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9c32834d44a72c7af793867f71a4d367141fc24ccb08e084b8cd7458eac47b3e -->
**`jiuwenswarm/agents/harness/common/rails/browser_task_prompt_rail.py`**

- 源码对模块职责的说明：Load-aware subagent prompt extension for browser delegation.。
- `BrowserTaskPromptRail` 继承 `SubagentRail`；方法入口：`__init__`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from openjiuwen.core.single_agent.rail.base import AgentCallbackContext`；`from openjiuwen.harness.rails.subagent import SubagentRail`；`from jiuwenswarm.agents.harness.common.prompt.browser_task_prompt import bu`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/browser_task_prompt_rail.py#L1-L49)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/eternal_conversation/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=696fc253d402635b0c1e0c2e0a2a75b6c6624db7d9960de0281e2985f23a6978 -->
**`jiuwenswarm/agents/harness/common/rails/eternal_conversation/__init__.py`**

- 源码对模块职责的说明：Eternal-conversation Rail public surface.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .rail import EternalConversationRail`；`from .registry import close_all_session_coordinators`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/__init__.py#L1-L6)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/eternal_conversation/background_agents.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eab97d59b36a79d86c8d8dbffe85e36d6b88ef8335cea5846a3aeb7539f29afe -->
**`jiuwenswarm/agents/harness/common/rails/eternal_conversation/background_agents.py`**

- 源码对模块职责的说明：Isolated model runners for Extractor (background 1) and Builder (background 2).。
- `BackgroundAgentRunner` 定义类型边界；方法入口：`__init__`, `set_model_supplier`, `call_json`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from typing import Any, Callable`；`from openjiuwen.core.foundation.llm.schema.message import SystemMessage, Us`。
- 模块级配置或常量名称：`MAX_BACKGROUND_ATTEMPTS`, `MAX_RETRY_RESPONSE_CHARS`, `RETRY_CHECKLIST`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/background_agents.py#L1-L138)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/eternal_conversation/coordinator.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=56b8b68392335badaf2e43de3a94b23a9fce78b462cce8a291c331cc07caec53 -->
**`jiuwenswarm/agents/harness/common/rails/eternal_conversation/coordinator.py`**

- 源码对模块职责的说明：Session-scoped Extractor/Builder scheduling and atomic publication.。
- `SessionCoordinator` 定义类型边界；方法入口：`__init__`, `closed`, `request_extract`, `resume_background`, `projection_for_boundary`, `mark_projection_applied`。
- 异步入口 `close_live_coordinators()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import contextvars`；`import hashlib`。
- 模块级配置或常量名称：`SNAPSHOT_LIMITS`, `MAX_TASKS_PER_EXTRACTION`, `PROTOCOL_STRING_INLINE_LIMIT`, `PROTOCOL_CONTAINER_INLINE_LIMIT`, `FROZEN_WORKING_MEMORY_INLINE_LIMIT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/coordinator.py#L1-L618)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/eternal_conversation/evidence.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f9f771be44b0823bc7b26ee7febbb79277230319cd011dc790016adb7a3874d1 -->
**`jiuwenswarm/agents/harness/common/rails/eternal_conversation/evidence.py`**

- 源码对模块职责的说明：Append-only, hash-chained evidence for eternal conversations.。
- 调用入口 `utc_now()`；声明返回 `str`。
- 调用入口 `jsonable(value)`；声明返回 `Any`。
- 调用入口 `read_json(path, default)`；声明返回 `Any`。
- 调用入口 `write_json_atomic(path, value)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import dataclasses`；`import hashlib`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/evidence.py#L1-L492)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0498e6272cad9e59344e854645faa08d412df5084855a8a05af0a0b751617005 -->
**`jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py`**

- 源码对模块职责的说明：Audited async gateway to the vendored dynamic-memory-cli contract.。
- `DynamicMemoryGateway` 定义类型边界；方法入口：`__init__`, `ensure_initialized`, `call`, `abort`, `file_command`, `search`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`import os`。
- 模块级配置或常量名称：`VENDORED_SKILL`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/memory_cli.py#L1-L139)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/eternal_conversation/prompts.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4a0efa96a05814843d4e1c91118def113518bbeb5e49e076afa89f0fd16d5411 -->
**`jiuwenswarm/agents/harness/common/rails/eternal_conversation/prompts.py`**

- 源码对模块职责的说明：Versioned prompts for the Persist Session foreground and workers.。
- 调用入口 `render_memory_context(session_root, projection, relevant_memory)`；声明返回 `str`。
- 调用入口 `prompt_hashes()`；声明返回 `dict[str, str]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import json`；`from pathlib import Path`。
- 模块级配置或常量名称：`EXTRACTOR_SYSTEM_PROMPT`, `BUILDER_SYSTEM_PROMPT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/prompts.py#L1-L201)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/eternal_conversation/rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=68eab1318b1aba4d17bd49a3257c7aafcbbe1b39cd71abe7c356304f22650a5f -->
**`jiuwenswarm/agents/harness/common/rails/eternal_conversation/rail.py`**

- 源码对模块职责的说明：Pluggable, inert-by-default eternal-conversation Rail.。
- `EternalConversationRail` 继承 `DeepAgentRail`；方法入口：`__init__`, `init`, `uninit`, `configure_runtime`, `before_invoke`, `on_user_message`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import uuid`。
- 模块级配置或常量名称：`FOREGROUND_CONTEXT_REPLACEMENT_MESSAGE_LIMIT`, `FOREGROUND_CONTEXT_REPLACEMENT_BYTE_LIMIT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/rail.py#L1-L420)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/eternal_conversation/registry.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9325bdf4ae4a3be4a793851cdabc776aa1a2792bd85eb39ea41fc3a1b0e4b408 -->
**`jiuwenswarm/agents/harness/common/rails/eternal_conversation/registry.py`**

- 源码对模块职责的说明：Process-level Session ownership for eternal-conversation coordinators.。
- 调用入口 `get_session_coordinator(root, session_id, model_supplier)`；声明返回 `SessionCoordinator`。
- 异步入口 `close_all_session_coordinators()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from pathlib import Path`；`from typing import Any, Callable`；`from weakref import WeakValueDictionary`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/eternal_conversation/registry.py#L1-L46)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/execution_guard/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=61285e7465bbc7c6530a5f5b954695d75b70e8352f7c585f4a050b7a1df54348 -->
**`jiuwenswarm/agents/harness/common/rails/execution_guard/__init__.py`**

- 集成依赖（导入声明，不等于全部运行时依赖）：`from .circuit_breaker_rail import CircuitBreakerConfig, CircuitBreakerRail`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/execution_guard/__init__.py#L1-L8)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/execution_guard/circuit_breaker_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f65560b64a95e52c410185036235b97ba9d4efc0f657f44b924b8c8596f5b061 -->
**`jiuwenswarm/agents/harness/common/rails/execution_guard/circuit_breaker_rail.py`**

- 源码对模块职责的说明：CircuitBreakerRail - Agent 循环检测断路器.。
- `CircuitBreakerConfig` 定义类型边界；方法入口：`history_size`。
- `ToolResultErrorDetector` 定义类型边界；方法入口：`register_plain_error_prefix`, `has_error`, `has_explicit_success`, `ctx_has_error`, `infer_record_has_error`。
- `ToolCallRecord` 定义类型边界。
- `DetectionResult` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import contextvars`；`import hashlib`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/execution_guard/circuit_breaker_rail.py#L1-L658)。
<!-- /kb:file -->
