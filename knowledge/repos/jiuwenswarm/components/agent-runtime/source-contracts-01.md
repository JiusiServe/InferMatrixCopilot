---
title: "agent-runtime 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# agent-runtime 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/runtime/agent_definition.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=75a880cc7b4c3c15b15713eefaa3e32061360bc17ac40406995180b8eb1dad9f -->
**`jiuwenswarm/runtime/agent_definition.py`**

- 源码对模块职责的说明：Transport-neutral contracts for one root Agent definition.。
- `RuntimeAgentDefinitionErrorCode` 继承 `str, Enum`。
- `RuntimeAgentDefinitionError` 继承 `ValueError`；方法入口：`__init__`。
- `RuntimeAgentMode` 继承 `str, Enum`。
- `RuntimeAgentDefinition` 定义类型边界；方法入口：`from_mapping`, `to_dict`, `fingerprint`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import json`；`import re`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/agent_definition.py#L1-L326)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/runtime/context.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=db2913d9306fa4eaa392316f3fbb609b4a1445e7b640d5554f5e2559b332a0ac -->
**`jiuwenswarm/runtime/context.py`**

- 源码对模块职责的说明：Task-local access to the Runtime currently executing an agent request.。
- `RuntimeExecutionContext` 定义类型边界。
- 调用入口 `set_runtime_context(runtime, agent_manager)`；声明返回 `Token[RuntimeExecutionContext / None]`。
- 调用入口 `reset_runtime_context(token)`；声明返回 `None`。
- 调用入口 `get_runtime_context()`；声明返回 `RuntimeExecutionContext / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from contextvars import ContextVar, Token`；`from dataclasses import dataclass`；`from typing import TYPE_CHECKING`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/context.py#L1-L70)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/runtime/events.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f537d35029b8784cfaefe4d8d6f0dba3bebe7f304998abf0bc55d7bdb1ba36a0 -->
**`jiuwenswarm/runtime/events.py`**

- 源码对模块职责的说明：Transport-neutral events emitted by the shared Agent Runtime.。
- `RuntimeEvent` 定义类型边界；方法入口：`event_type`, `to_dict`, `from_agent_message`, `control`, `error`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import asdict, dataclass`；`from typing import Any`。
- 模块级配置或常量名称：`TERMINAL_ERROR_EVENT_TYPES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/events.py#L1-L135)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/runtime/evolution.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=54364a38a9f2e74f8c837dd84363b00ce818dd435cdd579ea72bc1b5e03bd008 -->
**`jiuwenswarm/runtime/evolution.py`**

- 源码对模块职责的说明：Transport-neutral evolution approval payload predicates.。
- 调用入口 `is_evolution_approval_request_id(request_id)`；声明返回 `bool`。
- 调用入口 `is_evolution_approval_payload(payload)`；声明返回 `bool`。
- 调用入口 `is_interrupt_evolution_approval_answer_payload(payload)`；声明返回 `bool`。
- 调用入口 `ensure_regular_evolution_approval_metadata(payload)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`。
- 模块级配置或常量名称：`SKILL_EVOLUTION_APPROVAL_SCHEMA`, `SKILL_EVOLUTION_APPROVAL_SOURCE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/evolution.py#L1-L79)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/runtime/host_services.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=39f002a8887d56f95fe91e35e760e47acd34deb6b128c8a9caa28c7da725ee6d -->
**`jiuwenswarm/runtime/host_services.py`**

- 源码对模块职责的说明：Optional host capabilities injected into the transport-neutral Runtime.。
- 调用入口 `install_runtime_push_handler(handler)`；声明返回 `RuntimePushHandler / None`。
- 调用入口 `restore_runtime_push_handler(handler, previous)`；声明返回 `None`。
- 异步入口 `send_runtime_push(message)`；声明返回 `bool`。
- `RuntimeHostPushTransport` 定义类型边界；方法入口：`send_push`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import inspect`；`import threading`；`from collections.abc import Awaitable, Callable`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/host_services.py#L1-L194)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/runtime/interaction.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d58a24894c38f77e13f182a2934e34145aa7a9cf1437353650da950ccd4b1fa2 -->
**`jiuwenswarm/runtime/interaction.py`**

- 源码对模块职责的说明：Transport-neutral input for answering a Runtime interaction.。
- `InteractionAnswerError` 继承 `ValueError`。
- `InteractionAnswerInput` 定义类型边界；方法入口：`resumes_interrupted_turn`, `to_agent_request`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Mapping, Sequence`；`from copy import deepcopy`；`from dataclasses import dataclass`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/interaction.py#L1-L204)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/runtime/mcp_references.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9de7b9e1ab42004f1ffcc6a0811d96c4c1d98bf7710c8406cebbcdde6a0f8f6b -->
**`jiuwenswarm/runtime/mcp_references.py`**

- 源码对模块职责的说明：Read-only, transport-neutral validation of Runtime MCP references.。
- `McpReferenceStatus` 继承 `str, Enum`。
- `McpReferenceValidationError` 继承 `ValueError`。
- `McpReferenceInventoryError` 继承 `RuntimeError`。
- `McpReferenceValidationInput` 定义类型边界；方法入口：`from_iterable`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import re`；`from collections.abc import Callable, Iterable, Mapping`；`from dataclasses import dataclass`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/mcp_references.py#L1-L279)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/runtime/model_catalog.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1454d691a88e7c9fc05daa036ec3c4dc6bf1faced23e0f9d54cba759028efed9 -->
**`jiuwenswarm/runtime/model_catalog.py`**

- 源码对模块职责的说明：Transport-neutral, credential-free Runtime model catalog contracts.。
- `ModelCatalogError` 继承 `RuntimeError`；方法入口：`__init__`。
- `RuntimeModelDescriptor` 定义类型边界；方法入口：`to_dict`。
- `ModelCatalogResult` 定义类型边界；方法入口：`to_dict`。
- `ModelSelectionResult` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Iterable, Mapping, Sequence`；`from dataclasses import dataclass, replace`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/model_catalog.py#L1-L271)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/runtime/permission_catalog.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a8ca6fed6be921ac8e368a0905856a05cf2c50d9def966647975d54a26c0434c -->
**`jiuwenswarm/runtime/permission_catalog.py`**

- 源码对模块职责的说明：Read-only, transport-neutral permission snapshot contracts.。
- `PermissionCatalogError` 继承 `RuntimeError`；方法入口：`__init__`。
- `PermissionSnapshotInput` 定义类型边界。
- `PermissionToolSnapshot` 定义类型边界；方法入口：`to_dict`。
- `PermissionRuleSnapshot` 定义类型边界；方法入口：`to_dict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Mapping`；`from dataclasses import dataclass`；`from typing import Any, Literal, cast`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/permission_catalog.py#L1-L295)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/runtime/plan.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=04660f181493055aab474359846903746aab588b3da34c95c7540c86c32fd503 -->
**`jiuwenswarm/runtime/plan.py`**

- 源码对模块职责的说明：Plan-mode orchestration shared by AgentServer and process-style CLI.。
- `PlanStateResult` 定义类型边界。
- `PlanModeController` 定义类型边界；方法入口：`__init__`, `sync_locks`, `exited_sessions`, `active_sessions`, `reset_session`, `should_sync`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import inspect`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/plan.py#L1-L284)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/runtime/request.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=433a4bd1b4e9f78b14aba0339c1a36f072ad9295ab9952dcf269aee902c8fed2 -->
**`jiuwenswarm/runtime/request.py`**

- 源码对模块职责的说明：Transport-independent request normalization for the shared Runtime.。
- 调用入口 `resolve_request_project_dir(request, include_legacy_fallbacks)`；声明返回 `str / None`。
- 调用入口 `sync_chat_request_metadata(request, project_dir, mode, explicit_mode_provided, user_id)`；声明返回 `str / None`。
- 调用入口 `resolve_agent_request_mode(raw_mode, work_mode)`；声明返回 `tuple[str, str / None, str]`。
- 调用入口 `resolve_request_runtime_mode(request, work_mode)`；声明返回 `ResolvedMode`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import datetime as dt`；`import logging`；`import os`。
- 模块级配置或常量名称：`PREVIOUS_SESSION_MODE_KEY`, `CHAT_TURN_METHODS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/request.py#L1-L595)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/runtime/session_delete.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a478f2edd8183820e2cdb7b4465ef119298d4e3e3d1b353e555abca2e0bb9d1a -->
**`jiuwenswarm/runtime/session_delete.py`**

- 源码对模块职责的说明：Permanent Session deletion contracts owned by :class:'AgentRuntime'.。
- `SessionDeleteResult` 定义类型边界；方法入口：`failure`。
- `TeamDeleteResult` 定义类型边界。
- `TeamExecutionController` 继承 `Protocol`；方法入口：`quiesce_for_delete`, `dispose_after_resource_release`, `delete_aborted`, `delete_committed`。
- `TeamDeletionInProgress` 继承 `RuntimeError`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`from dataclasses import dataclass`；`from typing import Protocol`。
- 模块级配置或常量名称：`TEAM_DELETION_GATE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/session_delete.py#L1-L146)。
<!-- /kb:file -->
