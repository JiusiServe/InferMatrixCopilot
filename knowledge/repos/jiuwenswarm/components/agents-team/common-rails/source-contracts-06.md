---
title: "common-rails 源码接口与集成边界 06"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-rails 源码接口与集成边界 06

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/root_context.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=276e99becdc4a907111fdfbaa80e8a5e4b7c1345374caa099da8bb94f1bcb961 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/root_context.py`**

- 源码对模块职责的说明：Compact root-only authority for one permission decision.。
- `RootIntentTurnKind` 定义类型边界。
- `RootAskUserOption` 定义类型边界；方法入口：`to_mapping`, `from_mapping`。
- `RootAskUserClarification` 定义类型边界；方法入口：`to_mapping`, `from_mapping`。
- `RootIntentTurn` 定义类型边界；方法入口：`to_mapping`, `from_mapping`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from collections.abc import Iterable, Mapping`；`from contextvars import ContextVar, Token`。
- 模块级配置或常量名称：`ROOT_CONTEXT_KEY`, `HOST_USER_MESSAGE_SOURCE`, `ROOT_INTENT_MAX_TURNS`, `ROOT_INTENT_MAX_TURN_CHARS`, `ROOT_INTENT_MAX_TOTAL_CHARS`, `AUTO_REVIEW_BLOCK_INTENT_INPUT_TOO_LARGE`, `AUTO_REVIEW_BLOCK_HISTORY_WINDOW_TRUNCATED`, `HOST_USER_PROMPT_PREFIX_ZH`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/root_context.py#L1-L528)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/root_context_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1e926ada51d96baafc766e4904a0971610685e5e318b58eee9eab289db9579a6 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/root_context_rail.py`**

- 源码对模块职责的说明：Bind the compact root permission context inside OpenJiuwen callbacks.。
- `RootContextRail` 继承 `DeepAgentRail`；方法入口：`__init__`, `before_invoke`, `after_invoke`, `before_task_iteration`, `after_task_iteration`, `before_tool_call`。
- 调用入口 `put_permission_owner_in_inputs(inputs, owner)`；声明返回 `dict[str, Any]`。
- 调用入口 `root_context_failure_from_context(ctx)`；声明返回 `str / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Mapping`；`from contextvars import ContextVar`；`from dataclasses import dataclass`。
- 模块级配置或常量名称：`ROOT_CONTEXT_RAIL_PRIORITY`, `ROOT_CONTEXT_FAILURE_ATTRIBUTE`, `ROOT_PERMISSION_OWNER_KEY`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/root_context_rail.py#L1-L403)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/root_permission_queue_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=61a7530406fe4640d1627f8bdbabe7da208bb388f630834ec58698b0ea123489 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/root_permission_queue_rail.py`**

- 源码对模块职责的说明：Root tool identity rail and missing-sibling permission latch.。
- `RootPermissionRequestBinding` 定义类型边界。
- `RootPermissionResume` 定义类型边界。
- `RootNonPermissionResume` 定义类型边界。
- `RootPermissionWrapperResume` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Callable, Mapping`；`from contextvars import ContextVar, Token`；`from copy import deepcopy`。
- 模块级配置或常量名称：`ROOT_PERMISSION_QUEUE_PRIORITY`, `ROOT_PERMISSION_COMPLETION_PRIORITY`, `ROOT_PERMISSION_QUEUE_USER_INPUT_KEY`, `ROOT_NON_PERMISSION_RESUME_DTO_KEY`, `TOOL_INVOCATION_CONTEXT_ATTRIBUTE`, `ROOT_PERMISSION_RESUME_ATTRIBUTE`, `ROOT_NON_PERMISSION_RESUME_ATTRIBUTE`, `ROOT_PERMISSION_WRAPPERS_KEY`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/root_permission_queue_rail.py#L1-L517)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/sandbox_profile.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9796d7d65ba61fd708346362b9ce235e07770fe130db73d088858d68166a672e -->
**`jiuwenswarm/agents/harness/common/rails/permissions/sandbox_profile.py`**

- 源码对模块职责的说明：Sandbox operation-context extraction for auto permissions.。
- `SandboxDescriptor` 定义类型边界。
- 调用入口 `build_sandbox_profile(sys_operation)`；声明返回 `SandboxDescriptor`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Mapping`；`from dataclasses import dataclass`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/sandbox_profile.py#L1-L48)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/send_file_approval_scope.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d27a866af33bdca13cf84a5c2c4ce07fc9d62293aef09fee553e300e6c4331d -->
**`jiuwenswarm/agents/harness/common/rails/permissions/send_file_approval_scope.py`**

- 源码对模块职责的说明：Human approval scopes for file delivery path decisions.。
- `SendFileApprovalOutcome` 定义类型边界。
- `SendFileSessionApprovalStore` 定义类型边界；方法入口：`__init__`, `remember`, `matches`, `clear_session`, `clear_all`。
- `SendFileHumanApprovalBridge` 定义类型边界；方法入口：`__init__`, `session_store`, `apply`。
- 调用入口 `parse_human_approval_scope(payload)`；声明返回 `HumanApprovalScope / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import threading`；`from collections.abc import Callable, Mapping`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/send_file_approval_scope.py#L1-L234)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/send_file_path_guard.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1be7c32d2cab84efe0a8af66f37560fa0bd1cc6fb114ac0f04aca68823a57b88 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/send_file_path_guard.py`**

- 源码对模块职责的说明：Adapt multi-path file delivery to OpenJiuwen ''file_guard'' reads.。
- `SendFilePathGuardResult` 定义类型边界。
- `SendFilePathGuardEvaluator` 定义类型边界；方法入口：`evaluate`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`from collections.abc import Mapping, Sequence`。
- 模块级配置或常量名称：`SEND_FILE_TOOL_NAME`, `SEND_FILE_PATH_ARGUMENT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/send_file_path_guard.py#L1-L315)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/session_deny.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1f04dc8fddb5aafaaced8e0dfc80d03a406e6d31c5fde781464e3a3beddcb22e -->
**`jiuwenswarm/agents/harness/common/rails/permissions/session_deny.py`**

- 源码对模块职责的说明：Session-scoped denial records for auto permissions.。
- `SessionDenyRecord` 定义类型边界。
- `SessionDenyStore` 定义类型边界；方法入口：`__init__`, `record_denial`, `matches`。
- 调用入口 `evaluate_session_deny(store, session_id, tool_name, tool_args)`；声明返回 `DecisionRoute / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import json`；`from collections.abc import Mapping`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/session_deny.py#L1-L111)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/tool_binding.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=878f467db090a7949a4ae1b16176719e850810bcf07cf0f1ad83fbd095335ed5 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/tool_binding.py`**

- 源码对模块职责的说明：Read the current executable binding without making permission decisions.。
- 调用入口 `matches_bound_method(method, expected_owner, expected_func)`；声明返回 `bool`。
- 调用入口 `resolve_tool_binding(agent, tool_name, expected_type)`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from openjiuwen.core.runner import Runner`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/tool_binding.py#L1-L25)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/tool_capabilities.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=97576286efc9c32cb38066a3fc87770d393306239f3e8ee4c188c8d92a1caf7f -->
**`jiuwenswarm/agents/harness/common/rails/permissions/tool_capabilities.py`**

- 源码对模块职责的说明：Security-relevant tool capability taxonomy for auto permissions.。
- `ToolCapability` 定义类型边界。
- 调用入口 `shell_tool_names()`；声明返回 `list[str]`。
- 调用入口 `normalize_tool_name(tool_name)`；声明返回 `str`。
- 调用入口 `classify_tool(tool_name)`；声明返回 `ToolCapability`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from jiuwenswarm.common.permission_tools import PERMISSION_TOOL_ALIASES, Pe`。
- 模块级配置或常量名称：`TOOL_CAPABILITY_FACTS_VERSION`, `HOST_STATIC_FACTS`, `NAME_CLASSIFICATION_HINT`, `UNKNOWN_FACTS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/tool_capabilities.py#L1-L612)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/tool_decision_facts.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ba9911d4355b73c60b0c06ecf0317776e37fe9be694e585f5cb764f6492b1b30 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/tool_decision_facts.py`**

- 源码对模块职责的说明：Thin Host facts for one already-normalized root tool call.。
- `ToolDecisionFacts` 定义类型边界；方法入口：`tool_name`, `tool_category`, `paths`。
- `DecisionRoute` 定义类型边界；方法入口：`is_hard_block`, `requires_manual`, `requires_reviewer`, `is_deterministic_allow`, `accepted`, `allowed_outcomes`。
- 调用入口 `build_tool_decision_facts(tool_name, tool_args, workspace_root, platform_trusted_root, original_args_were_valid_object, external_paths, send_paths)`；声明返回 `ToolDecisionFacts`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Mapping, Sequence`；`from dataclasses import dataclass`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/tool_decision_facts.py#L1-L179)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/tool_invocation_key.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a7618bf07a7504858950b6cb5927392ffd74f16794573b8151e83cdc45c4f4b6 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/tool_invocation_key.py`**

- 源码对模块职责的说明：Host-owned identity and lifecycle state for one logical tool invocation.。
- 调用入口 `normalize_tool_invocation_text(name, value, maximum)`；声明返回 `str`。
- `ToolInvocationKeyV1` 定义类型边界；方法入口：`to_wire`, `from_wire`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Mapping`；`from dataclasses import dataclass`；`from typing import Any, Literal, TypeAlias`。
- 模块级配置或常量名称：`TOOL_INVOCATION_KEY_VERSION`, `MAX_TOOL_INVOCATION_ID_LENGTH`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/tool_invocation_key.py#L1-L94)。
<!-- /kb:file -->
