---
title: "common-rails 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-rails 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/interrupt/interrupt_helpers.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=150eeaab79ec66aad1efafead8975bf9b68bb0d6c88f6a33d6aa0239e71102a6 -->
**`jiuwenswarm/agents/harness/common/rails/interrupt/interrupt_helpers.py`**

- 源码对模块职责的说明：Interrupt helpers for DeepAgent.。
- 调用入口 `resolve_permission_workspace_dir(session_id)`；声明返回 `Path`。
- 调用入口 `merge_permission_trusted_dirs(trusted_dirs, project_dir)`；声明返回 `list[str]`。
- 调用入口 `apply_permission_trusted_dirs(rail, trusted_dirs, project_dir)`；声明返回 `None`。
- 调用入口 `has_interrupt_resume_payload(params)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import copy`；`import json`；`import re`。
- 模块级配置或常量名称：`SKILL_EVOLUTION_APPROVAL_SCHEMA`, `EVOLUTION_INTERRUPT_SOURCE`, `LEGACY_SKILL_EVOLUTION_APPROVAL_SOURCE`, `INTERRUPT_RESUME_SOURCES`, `EVOLUTION_INTERRUPT_METADATA_SOURCES`, `SKILL_EVOLUTION_APPROVAL_TOOL_KINDS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/interrupt/interrupt_helpers.py#L1-L1508)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/interrupt/permission_options.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7f114448064020dc9549f0d6295c7268e76f8b0044d343caba3efa4657781738 -->
**`jiuwenswarm/agents/harness/common/rails/interrupt/permission_options.py`**

- 源码对模块职责的说明：权限/确认审批选项的统一词表。。
- 调用入口 `normalize_option_value(value)`；声明返回 `str`。
- 调用入口 `resolve_permission_action(value)`；声明返回 `str / None`。
- 调用入口 `is_keep_planning_value(value)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import re`。
- 模块级配置或常量名称：`ALLOW_ONCE`, `SESSION_ALLOW`, `ALWAYS_ALLOW`, `REJECT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/interrupt/permission_options.py#L1-L92)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/memory_forbidden_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1ac5ffef70229d884bae57c858bf4f5992b94a71abc75575c2517ab797907362 -->
**`jiuwenswarm/agents/harness/common/rails/memory_forbidden_rail.py`**

- 源码对模块职责的说明：Execution-time guard for sensitive information written to memory.。
- `MemoryForbiddenRail` 继承 `DeepAgentRail`；方法入口：`before_model_call`, `before_tool_call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from pathlib import PurePath`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/memory_forbidden_rail.py#L1-L255)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/multimodal_image_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d394d4af66fc1de895ea750244e19b1d5efcc4de9747eb5d202da93c6b43d227 -->
**`jiuwenswarm/agents/harness/common/rails/multimodal_image_rail.py`**

- 源码对模块职责的说明：Multimodal image input adaptation for Core model calls.。
- `MultimodalImageRail` 继承 `DeepAgentRail`；方法入口：`__init__`, `init`, `before_model_call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from openjiuwen.core.single_agent.rail.base import AgentCallbackContext`；`from openjiuwen.harness.rails.base import DeepAgentRail`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/multimodal_image_rail.py#L1-L60)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b40bbede7fae96014a4716ab7dd072798d2cbfdadabb61cf3a8a3c3e01de7c44 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/__init__.py`**

- 源码对模块职责的说明：Security and permission integration for AgentServer.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from importlib import import_module`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/__init__.py#L1-L95)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/artifact_authorization.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=959e3f23b76e3d1b19f0bffd30faa70e49a6a2eee47bbaa655ef4532c688d681 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/artifact_authorization.py`**

- 源码对模块职责的说明：Exact file-delivery authorization for Smart Approval decisions.。
- 调用入口 `has_user_file_delivery_prohibition(text)`；声明返回 `bool`。
- 调用入口 `is_file_delivery_action(facts)`；声明返回 `bool`。
- `AutoPermissionArtifactAuthorizationMixin` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import re`；`from collections.abc import Mapping`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/artifact_authorization.py#L1-L132)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/artifact_declaration.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a4c09f40acb29a8a37664bca81fe1e827b1201db7e40beb460bbf729b1835052 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/artifact_declaration.py`**

- 源码对模块职责的说明：Exact send-file argument helpers.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from pathlib import Path`；`from jiuwenswarm.agents.harness.common.rails.permissions.tool_decision_fact`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/artifact_declaration.py#L1-L15)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/artifact_tracking_capture.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=06480b0598e626961b2a473c8ca4782b0339fea95e74a832500d1b35496d0054 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/artifact_tracking_capture.py`**

- 源码对模块职责的说明：Generic after-tool capture for Auto Permission.。
- `AutoPermissionArtifactCaptureMixin` 定义类型边界；方法入口：`after_tool_call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.i`；`from jiuwenswarm.server.runtime.sandbox_no_host_fallback import clear_no_ho`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/artifact_tracking_capture.py#L1-L23)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/before_tool.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fd79077e3a1bd20823d1544b52e9142db3089d663d9cbc749a8a9b73998748f7 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/before_tool.py`**

- 源码对模块职责的说明：Migrated Auto Permission before tool slice.。
- `AutoPermissionBeforeToolMixin` 定义类型边界；方法入口：`before_tool_call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`from collections.abc import Mapping`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/before_tool.py#L1-L966)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/deny_response.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=efed4ce85ef095ecb2509e4beea8f0f746ac859ea3bd542a3e29f4c8535252eb -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/deny_response.py`**

- 源码对模块职责的说明：Migrated Auto Permission deny response slice.。
- `AutoPermissionDenyResponseMixin` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Mapping, MutableMapping`；`from typing import Any`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.d`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/deny_response.py#L1-L86)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/deterministic.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=067bce0d40c4d33702d1a033a87232b82438adf9c36cc03f3d5d295699fdf781 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/deterministic.py`**

- 源码对模块职责的说明：Migrated Auto Permission deterministic slice.。
- `AutoPermissionDeterministicMixin` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.m`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.r`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/deterministic.py#L1-L131)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/domain_grant_audit.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=accc110f48feb8ccec3b9e1b4f5830bb89d429fc92d7902e7210326e30121d5d -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/domain_grant_audit.py`**

- 源码对模块职责的说明：Compact fixed-domain routing and response handling.。
- `AutoPermissionDomainGrantAuditMixin` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.d`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.m`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/domain_grant_audit.py#L1-L162)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/domain_manual.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a46a7edf003463b849b6bebb5501e49e1fc256e0cd4e010c56c504bd7e19a8ce -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/domain_manual.py`**

- 源码对模块职责的说明：Compact permission response helpers shared by manual and deny paths.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Mapping`；`from typing import Any`；`from jiuwenswarm.agents.harness.common.rails.permissions.tool_decision_fact`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/domain_manual.py#L1-L43)。
<!-- /kb:file -->
