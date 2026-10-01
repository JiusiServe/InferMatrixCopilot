---
title: "runtime 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# runtime 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/runtime/agent_config_service.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c3e39441abe2cd467928968a66745f690247774ee80b4d61a45771ee06261a2d -->
**`jiuwenswarm/server/runtime/agent_config_service.py`**

- 源码对模块职责的说明：Agent 配置管理服务 — 管理内置和自定义 agent 定义的 CRUD 操作.。
- `AgentDefinition` 定义类型边界。
- `CreateAgentParams` 定义类型边界。
- `UpdateAgentParams` 定义类型边界。
- `AgentConfigService` 定义类型边界；方法入口：`__init__`, `list_agents`, `get_agent`, `create_agent`, `update_agent`, `delete_agent`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from dataclasses import dataclass, field`；`from pathlib import Path`。
- 模块级配置或常量名称：`BUILTIN_AGENTS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_config_service.py#L1-L539)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/agent_manager.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f71a8a5dacf0ddf63d75929066eef0d906970d17bfd79dcc6a4d0e3e18ad8b9 -->
**`jiuwenswarm/server/runtime/agent_manager.py`**

- 源码对模块职责的说明：AgentManager - 管理 Agent 实例.。
- 调用入口 `collapse_plan_sub_mode(mode, sub_mode)`；声明返回 `str`。
- `AgentManager` 定义类型边界；方法入口：`__init__`, `set_heartbeat_service`, `has_smart_permission_lifecycle`, `schedule_permissions_reload`, `wait_for_permissions_ready`, `build_permissions_external_input_context`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`import logging`。
- 模块级配置或常量名称：`ACP_DEFAULT_CAPABILITIES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_manager.py#L1-L2234)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/agent_warm_pool.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9f62b20d3c97ae78713a6d11a2e65f8fe3b1c92cb5a1c1b8fe808169d56ee9fc -->
**`jiuwenswarm/server/runtime/agent_warm_pool.py`**

- 源码对模块职责的说明：Process-local pool of session-bound, ready-to-run DeepAgent instances.。
- 调用入口 `prewarm_enabled_by_env()`；声明返回 `bool`。
- `WarmKey` 定义类型边界；方法入口：`agent_mode`, `agent_sub_mode`。
- `WarmRevision` 定义类型边界。
- `WarmSlot` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import hashlib`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_warm_pool.py#L1-L774)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/extension_package_manager.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=577dcbe31d6f6909ef2a993f9dad477bf3aa9c010edc0d4b3e7324566e93b305 -->
**`jiuwenswarm/server/runtime/extension_package_manager.py`**

- 源码对模块职责的说明：Agent_template / plugin package manager (catalog + lifecycle).。
- `AgentGroupPackageError` 继承 `ValueError`；方法入口：`__init__`。
- 调用入口 `get_equipment_resources_agent_templates_dir()`；声明返回 `Path / None`。
- 调用入口 `get_equipment_resources_agent_groups_dir()`；声明返回 `Path / None`。
- 调用入口 `get_equipment_resources_plugin_packages_dir()`；声明返回 `Path / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import base64`；`import io`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/extension_package_manager.py#L1-L4152)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/image_modality_warmup.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b47874ad6d288d218a0459a82702149760ffbe468966062ce6a573ab67c8f54a -->
**`jiuwenswarm/server/runtime/image_modality_warmup.py`**

- 源码对模块职责的说明：Warm the process-wide image-modality probe cache.。
- 异步入口 `warm_image_modality_cache(config_base, reason)`；声明返回 `None`。
- 异步入口 `refresh_image_modality_cache(config_base, reason)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/image_modality_warmup.py#L1-L207)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/model_compiler_adapter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eb95d0a2d81b69272b80577929d7968481154076da753d41f2cef8ea050b729a -->
**`jiuwenswarm/server/runtime/model_compiler_adapter.py`**

- 源码对模块职责的说明：Thin boundary from JiuwenSwarm resolved DTOs to agent-core's compiler.。
- 调用入口 `compile_model_selection(resolved)`；声明返回 `tuple[Any, Any]`。
- 调用入口 `build_model_from_selection(resolved)`；声明返回 `Any`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from jiuwenswarm.common.model_errors import MODEL_RUNTIME_UNAVAILABLE, Mode`；`from jiuwenswarm.common.model_selection import ResolvedModel, ResolvedSelec`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/model_compiler_adapter.py#L1-L38)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/model_routing_registry.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1bcf03cdfcf4f9cb36cac52b62dea04366300f6e5015563dbc286de5e26eae88 -->
**`jiuwenswarm/server/runtime/model_routing_registry.py`**

- 源码对模块职责的说明：Resolve stable business selections into Foundation compiler input DTOs.。
- `ModelExecutionContext` 定义类型边界。
- `ModelSelectionResolver` 定义类型边界；方法入口：`__init__`, `choose`, `resolve`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from typing import Callable`；`from jiuwenswarm.common.model_catalog import ModelCatalog`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/model_routing_registry.py#L1-L141)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/no_host_fallback_jiuwenbox.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bed16184321e63afec4d7e7df67ba5e9422e04bb7b4f9845a8fb629bd6c493d3 -->
**`jiuwenswarm/server/runtime/no_host_fallback_jiuwenbox.py`**

- 源码对模块职责的说明：JiuwenBox providers that honor one task-local no-host-fallback scope.。
- `NoHostFallbackJiuwenBoxFSProvider` 继承 `_NoHostFallbackMixin, JiuwenBoxFSProvider`。
- `NoHostFallbackJiuwenBoxShellProvider` 继承 `_NoHostFallbackMixin, JiuwenBoxShellProvider`。
- `NoHostFallbackJiuwenBoxCodeProvider` 继承 `_NoHostFallbackMixin, JiuwenBoxCodeProvider`。
- 调用入口 `install_no_host_fallback_jiuwenbox_providers()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import sys`；`from collections.abc import AsyncIterator, Awaitable, Callable`；`from functools import wraps`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/no_host_fallback_jiuwenbox.py#L1-L138)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/offline_session_cleanup.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1f44c0a022dbbbef1da1555f8019b8940547db8c60b0c7002bdd40c5057264f2 -->
**`jiuwenswarm/server/runtime/offline_session_cleanup.py`**

- 源码对模块职责的说明：Runtime-owned cleanup for persisted Sessions while AgentServer is offline.。
- 异步入口 `delete_offline_session(channel_id, session_id)`；声明返回 `SessionDeleteResult`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from jiuwenswarm.runtime.service import AgentRuntime`；`from jiuwenswarm.runtime.session_delete import SessionDeleteResult`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/offline_session_cleanup.py#L1-L50)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/opencode_zen.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6d1675f2d42cd519d65c8c178050a08438d94b6b4d9ec34a1a5c50b48792bc41 -->
**`jiuwenswarm/server/runtime/opencode_zen.py`**

- 源码对模块职责的说明：Opencode Zen free models, fetched live at startup and held in memory only.。
- 异步入口 `warm_zen_free_models(reason)`；声明返回 `None`。
- 调用入口 `get_zen_free_model_entries()`；声明返回 `list[dict[str, Any]]`。
- 调用入口 `get_zen_free_context_window()`；声明返回 `int`。
- 调用入口 `get_zen_default_free_model_entry()`；声明返回 `dict[str, Any] / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`import threading`。
- 模块级配置或常量名称：`ZEN_API_BASE`, `ZEN_MODELS_URL`, `ZEN_ANON_API_KEY`, `ZEN_CLIENT_HEADERS`, `MODELS_DEV_URL`, `DEFAULT_FREE_MODEL_ID`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/opencode_zen.py#L1-L562)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/proactive_adapter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f389f29dfa02606278af87986a6e4c484b100534586b5548657616d8521f49ae -->
**`jiuwenswarm/server/runtime/proactive_adapter.py`**

- 源码对模块职责的说明：ProactiveEngine 初始化与适配层。。
- 调用入口 `resolve_proactive_adapter(agent)`；声明返回 `Any / None`。
- `ProactiveTriggerRequest` 定义类型边界。
- 调用入口 `build_proactive_agent()`。
- 异步入口 `trigger_main_agent(server, request, agent_manager, push_transport)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`import time`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/proactive_adapter.py#L1-L451)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/sandbox_no_host_fallback.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ff3d9b4b5c9106b702f11aeca48cb7ffb4910849a3a77840e228a271cd1c115b -->
**`jiuwenswarm/server/runtime/sandbox_no_host_fallback.py`**

- 源码对模块职责的说明：Task-local execution scope that forbids sandbox-to-host fallback.。
- 调用入口 `no_host_fallback_required()`；声明返回 `bool`。
- 调用入口 `require_no_host_fallback()`；声明返回 `None`。
- 调用入口 `clear_no_host_fallback()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from contextvars import ContextVar`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/sandbox_no_host_fallback.py#L1-L38)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/team_binding_store.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=56189e50bc77565b474ecb7fa8d2aa77ae6d861724e1fc21687dc6300fad38b5 -->
**`jiuwenswarm/server/runtime/team_binding_store.py`**

- 源码对模块职责的说明：Persistent team entity bindings.。
- `TeamBindingStoreError` 继承 `ValueError`；方法入口：`__init__`。
- `TeamBinding` 定义类型边界；方法入口：`from_dict`, `to_dict`。
- 调用入口 `validate_team_name(team_name)`；声明返回 `str`。
- `TeamBindingStore` 定义类型边界；方法入口：`__init__`, `path`, `list`, `get`, `create`, `bind_session`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import re`；`import threading`。
- 模块级配置或常量名称：`TEAM_NAME_RE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/team_binding_store.py#L1-L326)。
<!-- /kb:file -->
