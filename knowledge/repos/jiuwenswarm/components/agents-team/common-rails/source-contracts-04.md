---
title: "common-rails 源码接口与集成边界 04"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-rails 源码接口与集成边界 04

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/auto_config.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=800c18408616651b830411c3aa45b922f74970079acc7f230f509214e321f54a -->
**`jiuwenswarm/agents/harness/common/rails/permissions/auto_config.py`**

- 源码对模块职责的说明：Runtime normalization for task-level auto permission mode.。
- 调用入口 `resolve_declared_auto_workspace(params, metadata)`；声明返回 `Path / None`。
- 调用入口 `supports_phase_auto_root(params)`；声明返回 `bool`。
- 调用入口 `resolve_permission_runtime_mode(permission_config)`；声明返回 `str`。
- 调用入口 `is_auto_permission_mode(permission_config)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import copy`；`import logging`；`from collections.abc import Mapping`。
- 模块级配置或常量名称：`MANUAL_PERMISSION_MODE`, `AUTO_PERMISSION_MODE`, `AUTO_PERMISSION_DEFAULT_OPTIONS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/auto_config.py#L1-L347)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/auto_decision.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=106b8719ea8489cbcde19e810773c91732a06afa9464693d628984f232de6344 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/auto_decision.py`**

- 源码对模块职责的说明：Auto-permission guard helpers.。
- 调用入口 `deterministic_guard_route(facts)`；声明返回 `DecisionRoute / None`。
- 调用入口 `generic_mcp_egress_evidence(facts)`；声明返回 `tuple[str, ...]`。
- 调用入口 `deterministic_domain_route(facts, original_user_intent, recent_url_sources, browser_runtime_security_profile)`；声明返回 `DecisionRoute / None`。
- 调用入口 `terminal_low_risk_route(facts)`；声明返回 `DecisionRoute / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import math`；`import re`；`from collections.abc import Mapping, Sequence`。
- 模块级配置或常量名称：`ALLOW_LEVEL`, `ASK_LEVEL`, `DENY_LEVEL`, `SEARCH_SKILL_TOOL`, `SEARCH_SKILL_SENSITIVE_QUERY_PATTERN`, `EGRESS_SECRET_KEY_PATTERN`, `EGRESS_SECRET_VALUE_PATTERN`, `GENERIC_MCP_UPLOAD_KEYS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/auto_decision.py#L1-L533)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/auto_permission_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b8533e4c1c0d44d8afc5fd9299becf325245245008954e58fc6cdd98b1f4722e -->
**`jiuwenswarm/agents/harness/common/rails/permissions/auto_permission_rail.py`**

- 源码对模块职责的说明：Auto-permission wrapper around the OpenJiuwen permission rail.。
- `AutoPermissionInterruptRail` 继承 `AutoPermissionLifecycleMixin, AutoPermissionBeforeToolMixin, AutoPermissionArtifactCaptureMixin, AutoPermissionReviewerOverrideConsumeMixin, AutoPermissionReviewerOverrideGateMixin, AutoPermissionReviewerExecutionMixin, AutoPermissionDeterministicMixin, AutoPermissionArtifactAuthorizationMixin, AutoPermissionDenyResponseMixin, AutoPermissionManualAuthorizationMixin, AutoPermissionDomainGrantAuditMixin, AutoPermissionRuntimeBridgeMixin, AgentRail`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from openjiuwen.core.single_agent.rail.base import AgentRail`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.a`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.a`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/auto_permission_rail.py#L1-L75)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/auto_reviewer.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c749ce409ff95f26e6146f4895f14b796fc2ccd1714fc5a531f8c9cbce81135b -->
**`jiuwenswarm/agents/harness/common/rails/permissions/auto_reviewer.py`**

- 源码对模块职责的说明：Locked-down task-level auto reviewer protocol.。
- `ReviewerOutcome` 定义类型边界。
- `ReviewerClient` 继承 `Protocol`；方法入口：`assess`。
- 调用入口 `build_isolated_reviewer_model(model)`；声明返回 `Any / None`。
- `IsolatedModelReviewerClient` 定义类型边界；方法入口：`__init__`, `assess`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import inspect`；`import json`。
- 模块级配置或常量名称：`AUTO_REVIEW_REASON_SUMMARY_LIMIT`, `AUTO_REVIEW_REASON_CODE_LIMIT`, `AUTO_REVIEW_PATH_TARGET_LIMIT`, `AUTO_REVIEW_PATH_LABEL_LIMIT`, `FORBIDDEN_REVIEWER_FIELDS`, `REQUIRED_REVIEWER_FIELDS`, `OPTIONAL_REVIEWER_FIELDS`, `ALLOWED_REVIEWER_FIELDS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/auto_reviewer.py#L1-L888)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/execution_provider_contract.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ce3d2d0e04218c70796f981b3accb90b6e7c9aabb16d04a7058bfffbd82e4bf8 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/execution_provider_contract.py`**

- 源码对模块职责的说明：Closed execution-provider contracts consumed by Auto Permission.。
- 调用入口 `requires_no_host_fallback(tool_name, tool_category)`；声明返回 `bool`。
- 调用入口 `requires_manual_execution_provider_review(tool_name, tool_category)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`。
- 模块级配置或常量名称：`JIUWENBOX_SANDBOX_EXECUTION_TOOLS`, `ACP_IDE_EXECUTION_TOOLS`, `UNKNOWN_PROVIDER_EXECUTION_TOOLS`, `EXECUTION_PROVIDER_CONTRACT_UNVERIFIED`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/execution_provider_contract.py#L1-L37)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/generated_artifact_delivery.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=55180e682a3b764ca29a53c2bc74d18382ac1321ebfd1de3d8187efcfd3b6396 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/generated_artifact_delivery.py`**

- 源码对模块职责的说明：Task-local authorization for one exact ''send_file_to_user'' call.。
- `SendFileAuthorizationItem` 定义类型边界。
- `SendFileExecutionGrant` 定义类型边界。
- 调用入口 `normalize_send_file_target_channels(value)`；声明返回 `tuple[str, ...]`。
- 调用入口 `normalize_send_file_paths(value)`；声明返回 `tuple[str, ...]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import contextvars`；`import json`；`import threading`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/generated_artifact_delivery.py#L1-L175)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/native_path_context.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d242800aa8342e70440681e1b90f0fe1368d1fec1389b758991d1dbeca2c81ef -->
**`jiuwenswarm/agents/harness/common/rails/permissions/native_path_context.py`**

- 源码对模块职责的说明：Smart-only, invocation-local projection of verified native file accesses.。
- `NativePathAccess` 定义类型边界；方法入口：`guard_tool`, `guard_args`。
- 调用入口 `native_arguments_json(args)`；声明返回 `str`。
- 调用入口 `current_native_path_access(tool_name, args)`；声明返回 `NativePathAccess / None`。
- `NativePathGuardProjection` 定义类型边界；方法入口：`__init__`, `evaluate`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from collections.abc import Mapping`；`from contextvars import ContextVar`。
- 模块级配置或常量名称：`NATIVE_PATH_ACCESS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/native_path_context.py#L1-L65)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/network_scope.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3a236823e3d2a08b4f918434d04f0437e6a337caf866f27e78b0c83918844f44 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/network_scope.py`**

- 源码对模块职责的说明：Shared network scope helpers for permission grants and read-only fetches.。
- 调用入口 `normalize_network_host(host)`；声明返回 `str`。
- 调用入口 `network_host_rejection_reason(host)`；声明返回 `str / None`。
- 调用入口 `host_matches_allowed_domain(host, allowed_domain)`；声明返回 `bool`。
- 调用入口 `has_secret_query(query)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import ipaddress`；`import re`；`from urllib.parse import parse_qsl`。
- 模块级配置或常量名称：`SECRET_QUERY_KEYS`, `SECRET_QUERY_COMPACT_KEYS`, `SECRET_QUERY_WORDS`, `SECRET_QUERY_KEY_QUALIFIERS`, `PUBLIC_SUFFIX_ONLY_HOSTS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/network_scope.py#L1-L175)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/openjiuwen_contract.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f0672666189360974aabf75c820c5cfeef92a56c421401ad7865390637b8eb4f -->
**`jiuwenswarm/agents/harness/common/rails/permissions/openjiuwen_contract.py`**

- 源码对模块职责的说明：Runtime contract helpers for openjiuwen permission rails.。
- `OpenJiuwenPermissionContract` 定义类型边界。
- 调用入口 `load_openjiuwen_permission_contract()`；声明返回 `OpenJiuwenPermissionContract`。
- 调用入口 `build_denied_permission_response(reason)`；声明返回 `Any`。
- 调用入口 `build_rejected_permission_response(reason)`；声明返回 `Any`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import inspect`；`from dataclasses import dataclass`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/openjiuwen_contract.py#L1-L183)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/permission_compose.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cf5ae08a3bd6aba938b187ff5e6c5e9432997426b7e1b9b666487a9c04c8e562 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/permission_compose.py`**

- 源码对模块职责的说明：Compose Global ⊕ User ⊕ Session into effective permissions for the Engine.。
- 调用入口 `compose_host_effective_permissions(global_permissions, user_permissions, session_permissions, session_id, agent_permissions)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from copy import deepcopy`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/permission_compose.py#L1-L349)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/project_memory/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8509b3dd4d91bae9c005384b23853370ba9ae6df4055eb7bc321584724d374f7 -->
**`jiuwenswarm/agents/harness/common/rails/project_memory/__init__.py`**

- 源码对模块职责的说明：Project memory helpers (file discovery + PromptSection factory).。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.agents.harness.common.rails.project_memory.files import AD`；`from jiuwenswarm.agents.harness.common.rails.project_memory.section import `。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/project_memory/__init__.py#L1-L47)。
<!-- /kb:file -->
