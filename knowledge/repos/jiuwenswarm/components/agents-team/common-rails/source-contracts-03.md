---
title: "common-rails 源码接口与集成边界 03"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-rails 源码接口与集成边界 03

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/invocation_context.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3d775d7dd6682ec7203347ccfb5107bd12e1f1816679ee068857d1f665916e2e -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/invocation_context.py`**

- 源码对模块职责的说明：Migrated Auto Permission invocation context slice.。
- 调用入口 `normalize_invocation_tool_args(tool_name, value)`；声明返回 `dict[str, Any]`。
- `TrustedSendIdentity` 定义类型边界。
- `TrustedSendIdentityResolution` 定义类型边界。
- 调用入口 `repair_malformed_tool_arguments(tool_args)`；声明返回 `dict[str, Any] / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from collections.abc import Mapping`；`from dataclasses import dataclass`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/invocation_context.py#L1-L715)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/lifecycle.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f76c0f8e6499b27136f5a581bb8af1325b394bfdf4e4baeb7b6edab5ca53400c -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/lifecycle.py`**

- 源码对模块职责的说明：Migrated Auto Permission lifecycle slice.。
- `AutoPermissionLifecycleMixin` 定义类型边界；方法入口：`__init__`, `init`, `uninit`, `get_tools`, `installed_permission_config`, `set_trusted_dirs`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Callable`；`from copy import deepcopy`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/lifecycle.py#L1-L180)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/manual_authorization.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=60795d1a39666aa8e8d1308767763096986012814f15d62847c0455d6a47664f -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/manual_authorization.py`**

- 源码对模块职责的说明：Migrated Auto Permission manual authorization slice.。
- `AutoPermissionManualAuthorizationMixin` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.d`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.i`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/manual_authorization.py#L1-L90)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/models.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=560bd945243f0560b0f48f95bfbe4c3b382b98050a28152c2d78981deb718394 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/models.py`**

- 源码对模块职责的说明：Migrated Auto Permission models slice.。
- `ToolInvocation` 定义类型边界。
- `PermissionHandlingResult` 定义类型边界。
- `PermissionInterruptRequest` 继承 `InterruptRequest`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import re`；`from dataclasses import dataclass`。
- 模块级配置或常量名称：`PROHIBITED_FILE_DELIVERY_REASON`, `DETERMINISTIC_BOUNDED_SCOPE_DECISION_SOURCE`, `DETERMINISTIC_READONLY_PUBLIC_WEB_REASON`, `DETERMINISTIC_READONLY_PUBLIC_WEB_FETCH_SOURCE_KINDS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/models.py#L1-L100)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/readonly_tool_bindings.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7125d0a0ca952d68d37454e1f642b0d8abdb0a4f8a27d899f04e649777393e0d -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/readonly_tool_bindings.py`**

- 源码对模块职责的说明：Executable identities for the closed builtin observation fast path.。
- 调用入口 `trusted_readonly_binding(invocation, session_id)`；声明返回 `bool`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from types import CodeType, FunctionType`；`from openjiuwen.core.foundation.tool import LocalFunction`；`from openjiuwen.core.foundation.tool.base import _ToolMeta`；`from openjiuwen.core.runner.callback import decorator as callbacks`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/readonly_tool_bindings.py#L1-L110)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_audit.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e49afbc5e540ee8c4f2a630041d13a3ad703ea19d541127dd82a178142ed6dfd -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_audit.py`**

- 源码对模块职责的说明：Migrated Smart Approval reviewer audit helpers.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from collections.abc import Mapping`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_audit.py#L1-L94)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_execution.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=434a43e779a6d5cee80203b86dc94b1f48df5ef0f20d9c3a085dde4a9886596a -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_execution.py`**

- 源码对模块职责的说明：Migrated Auto Permission reviewer execution slice.。
- `AutoPermissionReviewerExecutionMixin` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.m`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.r`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_execution.py#L1-L389)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_metadata.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f254ab73fbbf89d40b25b5e546ef37576de9d62ee4ed226c10746a3afc1c9899 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_metadata.py`**

- 源码对模块职责的说明：Compact Host-owned projection for Reviewer audit and UI metadata.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Mapping`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.m`；`from jiuwenswarm.agents.harness.common.rails.permissions.reviewer_redaction`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_metadata.py#L1-L360)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_override_consume.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5ce912a1fe2cf0bd3238e5b196549b560b95fb8e60612dfe9b7b0db135e7cb0f -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_override_consume.py`**

- 源码对模块职责的说明：Consume one exact RootPermissionQueue Auto manual approval.。
- `AutoPermissionReviewerOverrideConsumeMixin` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from openjiuwen.core.single_agent.interrupt.state import INTERRUPT_AUTO_CON`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.m`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_override_consume.py#L1-L122)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_override_gate.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9001e8d48ffdf983c8e79185e9db128e22fa71912786db0d7b35c3aec34659ba -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_override_gate.py`**

- 源码对模块职责的说明：Migrated Auto Permission reviewer override gate slice.。
- `AutoPermissionReviewerOverrideGateMixin` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.r`；`from jiuwenswarm.agents.harness.common.rails.permissions._auto_permission.r`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/reviewer_override_gate.py#L1-L67)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/runtime_bridge.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9bbbaa150a346179bbf8659fb77f2217969d851d07fc9b1aa08937b2036ed1ba -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/runtime_bridge.py`**

- 源码对模块职责的说明：Migrated Auto Permission runtime bridge slice.。
- `AutoPermissionRuntimeBridgeMixin` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import inspect`；`from collections.abc import Mapping, MutableMapping`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/runtime_bridge.py#L1-L311)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/runtime_result.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a0743017314796837e17ea2fcce836b0b231998189b316e1d3225b22af539ba3 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/runtime_result.py`**

- 源码对模块职责的说明：Migrated Auto Permission runtime result slice.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import inspect`；`import re`；`from collections.abc import Callable, Mapping`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/_auto_permission/runtime_result.py#L1-L250)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rails/permissions/audit.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e7512a0c35b50c9760eff135b9c1b5f76118b51182ca4489deccbc84b1e5d882 -->
**`jiuwenswarm/agents/harness/common/rails/permissions/audit.py`**

- 源码对模块职责的说明：Observe-only audit logging for auto permissions.。
- 调用入口 `emit_permission_audit(facts, decision, reason, degraded, grant_id, grant_reason, extra, persistent_writer)`；声明返回 `Any / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rails/permissions/audit.py#L1-L65)。
<!-- /kb:file -->
