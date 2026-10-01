---
title: "common-core 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-core 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/common/kv_cache_affinity_config.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2d18f7da40d8e1b89370ddb28448996fb96e91f926c1479486a5c4ef446b62c4 -->
**`jiuwenswarm/common/kv_cache_affinity_config.py`**

- 源码对模块职责的说明：Canonical configuration and provider rules for KV cache affinity.。
- 调用入口 `is_kv_cache_affinity_config(config_like)`；声明返回 `bool`。
- 调用入口 `normalize_provider(provider)`；声明返回 `str`。
- 调用入口 `has_kv_cache_affinity_capability(model_client_config, provider)`；声明返回 `bool`。
- 调用入口 `model_provider(model)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import os`；`from typing import Any`。
- 模块级配置或常量名称：`ASCEND_AFFINITY_PROVIDER`, `APPLICATION_KV_CACHE_CONFIG_KEY`, `KV_CACHE_AFFINITY_ENABLED_KEY`, `KVC_CONFIG_KEYS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/kv_cache_affinity_config.py#L1-L264)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/media_capability_config.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a5c4f2965132cf5b338e66388ba79ca230b05e5b1f37920286e08b7982376b2f -->
**`jiuwenswarm/common/media_capability_config.py`**

- 源码对模块职责的说明：Startup migration for explicit multimodal capability switches.。
- 调用入口 `migrate_media_capability_switches(env_path, environ, lock_timeout)`；声明返回 `dict[str, str]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import stat`；`from collections.abc import MutableMapping`。
- 模块级配置或常量名称：`MEDIA_CAPABILITY_ENV_FIELDS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/media_capability_config.py#L1-L105)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/model_errors.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e22bd8a0485df4f7008056d94af8bc98e2b26b5ebb7b8e908ed46a91cf34ce10 -->
**`jiuwenswarm/common/model_errors.py`**

- 源码对模块职责的说明：Stable model-selection error codes shared by runtime and RPC layers.。
- `ModelSelectionError` 继承 `RuntimeError`；方法入口：`__init__`, `to_payload`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`。
- 模块级配置或常量名称：`MODEL_SELECTION_NOT_FOUND`, `MODEL_SELECTION_DISABLED`, `MODEL_SELECTION_FORBIDDEN`, `MODEL_GROUP_INVALID`, `MODEL_GROUP_NO_AVAILABLE_ROUTE`, `MODEL_REQUEST_CONFIG_INVALID`, `MODEL_ROUTE_FAILED`, `MODEL_STREAM_INTERRUPTED`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/model_errors.py#L1-L30)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/model_migration.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=378bf80432a2346f1b13fccc75ccae5bbbba0849292c89064bfe314d345ad352 -->
**`jiuwenswarm/common/model_migration.py`**

- 源码对模块职责的说明：One-time, idempotent migration from unambiguous model names to stable IDs.。
- 调用入口 `migrate_legacy_model_selections()`；声明返回 `dict[str, int]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import os`；`import uuid`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/model_migration.py#L1-L79)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/model_vendor_registry.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c10372e8382345eea5f22261366ae4fa9d46d19d8c5da2705a7efa6d090e3be0 -->
**`jiuwenswarm/common/model_vendor_registry.py`**

- 源码对模块职责的说明：Model vendor preset registry.。
- `PlanKind` 继承 `str, Enum`。
- `VendorPreset` 定义类型边界。
- 调用入口 `get_presets_by_plan(plan)`；声明返回 `list[VendorPreset]`。
- 调用入口 `get_preset(vendor_key, plan)`；声明返回 `VendorPreset / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from dataclasses import dataclass`；`from enum import Enum`。
- 模块级配置或常量名称：`ANTHROPIC_CLIENT_PROVIDER`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/model_vendor_registry.py#L1-L571)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/openrouter_attribution.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=96a664e44156e02c8830fd3abb7a568b882e4dcf0e50d06008580053a46fa392 -->
**`jiuwenswarm/common/openrouter_attribution.py`**

- 调用入口 `is_openrouter_provider(provider)`；声明返回 `bool`。
- 调用入口 `is_openrouter_client_config(mcc)`；声明返回 `bool`。
- 调用入口 `inject_attribution_headers(mcc)`；声明返回 `dict[str, Any]`。
- 调用入口 `inject_attribution_to_config(config)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any, Optional`。
- 模块级配置或常量名称：`OPENROUTER_ATTRIBUTION_HEADERS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/openrouter_attribution.py#L1-L86)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/playwright_mcp_runtime.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=345af097c7bacd5632079b4bbef3882d404b2ae1fb7950086a3ec997908e0acc -->
**`jiuwenswarm/common/playwright_mcp_runtime.py`**

- 源码对模块职责的说明：Resolve and safely materialize the bundled Playwright MCP runtime.。
- `PlaywrightMcpRuntimeError` 继承 `RuntimeError`。
- `PlaywrightMcpLaunch` 定义类型边界。
- 调用入口 `parse_playwright_mcp_args(value)`；声明返回 `list[str]`。
- 调用入口 `serialize_playwright_mcp_args(args)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import json`；`import logging`。
- 模块级配置或常量名称：`PLAYWRIGHT_MCP_VERSION`, `MINIMUM_NODE_VERSION`, `PINNED_NPX_COMMAND`, `PINNED_NPX_ARGS`, `LEGACY_TEMPLATE_COMMAND`, `LEGACY_TEMPLATE_ARGS`, `MANIFEST_FILENAME`, `INTERNAL_SOURCE_ENV`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/playwright_mcp_runtime.py#L1-L411)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/process_supervision.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=719ea8d7fada0a54e770394a56f0ea8f26cd3bbc08972cb1d56e269d2ab973d4 -->
**`jiuwenswarm/common/process_supervision.py`**

- 源码对模块职责的说明：Supervise the AgentServer and Gateway children of ''jiuwenswarm.app''.。
- 调用入口 `is_crash_exit(returncode)`；声明返回 `bool`。
- 调用入口 `supervise(commands, popen_kwargs)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import contextlib`；`import json`；`import logging`。
- 模块级配置或常量名称：`GATEWAY_RESTART_EXIT_CODE`, `CRASH_EXIT_CODE`, `SUPERVISOR_PID_ENV`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/process_supervision.py#L1-L306)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/projectless_workspace.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=21c325bb47c7fd20d0eb7b1288096df8f8bc9da2f3c782df6949fb1034f3ac4a -->
**`jiuwenswarm/common/projectless_workspace.py`**

- 源码对模块职责的说明：Cross-platform workspaces for Agent/Code requests without a project.。
- `ProjectlessTaskWorkspace` 定义类型边界。
- 调用入口 `get_projectless_tasks_dir()`；声明返回 `Path`。
- 调用入口 `get_projectless_task_workspace(session_id, task_name)`；声明返回 `ProjectlessTaskWorkspace`。
- 调用入口 `get_registered_projectless_task_root(session_id)`；声明返回 `Path / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import datetime as _datetime`；`import json`；`import math`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/projectless_workspace.py#L1-L508)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/protocol_ids.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=59c9bf42137e977e6f413c36a2de8ae9b5520c049594550238a8a4f8784cbcd4 -->
**`jiuwenswarm/common/protocol_ids.py`**

- 源码对模块职责的说明：Validation for externally supplied protocol identifiers.。
- `InvalidProtocolId` 继承 `ValueError`。
- 调用入口 `validate_session_id(value)`；声明返回 `str`。
- 调用入口 `is_valid_session_id(value)`；声明返回 `bool`。
- 调用入口 `validate_workflow_run_id(value)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import re`；`from typing import Any`。
- 模块级配置或常量名称：`SESSION_ID_MAX_LEN`, `WORKFLOW_RUN_ID_MAX_LEN`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/protocol_ids.py#L1-L67)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/reasoning_injector.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5cea9085cb1e58776e5ee75b0269211ca422f175bba99335ccb520c17f455d38 -->
**`jiuwenswarm/common/reasoning_injector.py`**

- 调用入口 `core_has_context_window_field()`；声明返回 `bool`。
- 调用入口 `inject_reasoning_params(model_client_config, model_config_obj)`；声明返回 `dict[str, Any]`。
- 调用入口 `build_reasoning_model_request_kwargs(model_client_config, model_config_obj, model_name)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Mapping`；`from typing import Any`；`from jiuwenswarm.common.reasoning_config import normalize_reasoning_level, `。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/reasoning_injector.py#L1-L172)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/runtime_log_filter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c8ee44f86814b4d31b92d29467acd4f94f2fd53ed821b268cd6f055fcfa51b15 -->
**`jiuwenswarm/common/runtime_log_filter.py`**

- 源码对模块职责的说明：Bound repeated DB and browser-health diagnostics without filtering other errors.。
- `RuntimeLogFilter` 继承 `logging.Filter`；方法入口：`__init__`, `filter`, `flush`。
- 调用入口 `install_runtime_log_filter()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import atexit`；`import logging`；`import threading`；`import time`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/runtime_log_filter.py#L1-L124)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/runtime_workspace.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7be2372b28ac97f5cd01b6b8032edd8d96e53563a0efc85b84da2c47591162af -->
**`jiuwenswarm/common/runtime_workspace.py`**

- 源码对模块职责的说明：Resolve internal and user-operable workspaces for single-agent modes.。
- `RuntimeWorkspacePaths` 定义类型边界。
- 调用入口 `resolve_runtime_workspace_paths(internal_workspace_dir, project_dir, workspace_dir, cwd, session_id, task_name, bind_request)`；声明返回 `RuntimeWorkspacePaths`。
- 调用入口 `bind_session_runtime_workspace(internal_workspace_dir, project_dir, session_id)`；声明返回 `RuntimeWorkspacePaths`。
- 调用入口 `resolve_bound_runtime_workspace_paths(binding, project_dir, workspace_dir, cwd)`；声明返回 `RuntimeWorkspacePaths`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass, replace`；`from pathlib import Path`；`from jiuwenswarm.common.projectless_workspace import get_projectless_task_w`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/runtime_workspace.py#L1-L148)。
<!-- /kb:file -->
