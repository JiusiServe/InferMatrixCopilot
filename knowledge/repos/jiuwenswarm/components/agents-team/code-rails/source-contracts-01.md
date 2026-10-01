---
title: "code-rails 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# code-rails 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9579e873fc40f9f2ecdcc1edbc68b78a5cb560b1231af8f1158622cb68e89352 -->
**`jiuwenswarm/agents/harness/code/rails/__init__.py`**

- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.agents.harness.code.rails.code_task_planning_rail import C`；`from jiuwenswarm.agents.harness.code.rails.code_plan_approval_interrupt_rai`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/__init__.py#L1-L13)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/code_agent_mode_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=097008ebb641dee5d73a09975e018e55e750365d10bfa638e08a19aa81cc541b -->
**`jiuwenswarm/agents/harness/code/rails/code_agent_mode_rail.py`**

- 源码对模块职责的说明：CodeAgentModeRail — plan-mode write enforcement for code mode.。
- `CodeAgentModeRail` 继承 `AgentModeRail`；方法入口：`init`, `before_tool_call`, `after_tool_call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import re`；`from typing import TYPE_CHECKING, Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_agent_mode_rail.py#L1-L292)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/code_confirm_interrupt_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=52dfe6fb09dfeaaa7a0686e1063533c5338b5fee3c7724e82fe5fcccbcb143b4 -->
**`jiuwenswarm/agents/harness/code/rails/code_confirm_interrupt_rail.py`**

- 源码对模块职责的说明：CodeConfirmInterruptRail — user-visible confirmation for sensitive control tools.。
- 调用入口 `build_confirm_interrupt_message(tool_name, tool_args)`；声明返回 `str`。
- `CodeConfirmInterruptRail` 继承 `ConfirmInterruptRail`；方法入口：`resolve_interrupt`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from typing import Any, Optional`；`from openjiuwen.core.foundation.llm.schema.tool_call import ToolCall`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_confirm_interrupt_rail.py#L1-L142)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/code_plan_approval_interrupt_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d9fa42c1eed9f8a0de3926a03c59e22ebb3c94d9e569d9cffa29e196cd3e49a1 -->
**`jiuwenswarm/agents/harness/code/rails/code_plan_approval_interrupt_rail.py`**

- 源码对模块职责的说明：PlanApprovalInterruptRail — instant plan approval dialog for exit_plan_mode.。
- 调用入口 `is_plan_approval_message(message)`；声明返回 `bool`。
- 调用入口 `strip_inline_plan_approval_choices(message)`；声明返回 `str`。
- 调用入口 `extract_plan_approval_content(message)`；声明返回 `tuple[str, str]`。
- 调用入口 `build_plan_approval_options_from_message(message)`；声明返回 `list[dict[str, str]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import TYPE_CHECKING, Any, Optional`；`from openjiuwen.core.common.logging import logger`；`from openjiuwen.core.foundation.llm.schema.tool_call import ToolCall`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_plan_approval_interrupt_rail.py#L1-L371)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/code_plan_approval_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3f110d0faa1cb53e043b5c7da3ada4d32d81745f9942856dd5e8ca14fec17fb6 -->
**`jiuwenswarm/agents/harness/code/rails/code_plan_approval_rail.py`**

- 源码对模块职责的说明：PlanApprovalRail — pending-approval lifecycle for plan mode exit.。
- `PlanApprovalState` 定义类型边界；方法入口：`to_dict`。
- `PlanApprovalRail` 继承 `DeepAgentRail`；方法入口：`init`, `uninit`, `before_model_call`, `before_tool_call`, `after_tool_call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from pathlib import Path`；`from typing import TYPE_CHECKING, Any`。
- 模块级配置或常量名称：`PENDING_EXIT_RESULT_PREFIX`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/code_plan_approval_rail.py#L1-L226)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/heartbeat/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=00cf2789a1877b1ba2a539ac8f11b3a93b18f85626cd7b5d35e9c416a3cd2bbc -->
**`jiuwenswarm/agents/harness/code/rails/heartbeat/__init__.py`**

- 源码对模块职责的说明：AgentServer-owned Heartbeat domain used by :mod:'heartbeat_rail'.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .controller import HeartbeatController`；`from .models import HeartbeatJob, HeartbeatSchedule`；`from .runtime import HeartbeatRuntimeUnavailableError`；`from .scheduler import HeartbeatSchedulerService`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/__init__.py#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7a1a577f8f852db745ddb0449da583db643eb064e619106bbefe02287d4f49e8 -->
**`jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py`**

- 源码对模块职责的说明：Heartbeat domain controller owned by the AgentServer Rail runtime.。
- `HeartbeatController` 定义类型边界；方法入口：`__init__`, `set_limits`, `limits`, `list_jobs`, `get_job`, `create_job`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import math`；`import time`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/controller.py#L1-L576)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/heartbeat/cron_schedule.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6a021f42b717222871805f769f26abe1d7772cb7d05ac0ff689a690ff455b266 -->
**`jiuwenswarm/agents/harness/code/rails/heartbeat/cron_schedule.py`**

- 源码对模块职责的说明：Shared Cron parsing and calculation for the Heartbeat domain.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.runtime.cron.cron_expr import next_cron_datetime, validate`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/cron_schedule.py#L1-L8)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/heartbeat/execution.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=be63b8450f465c5f6ce477e46e9c41a8a944e2e3ebc993ab9ff82e097fb85047 -->
**`jiuwenswarm/agents/harness/code/rails/heartbeat/execution.py`**

- 源码对模块职责的说明：Heartbeat admission and AgentServer-local execution.。
- `SessionRunAdmission` 定义类型边界；方法入口：`__init__`, `set_heartbeat_preemptor`, `is_user_active`, `active_heartbeat_sessions`, `is_heartbeat_active`, `has_pending_interaction`。
- `HeartbeatExecutionService` 定义类型边界；方法入口：`__init__`, `set_scheduler`, `set_completion_hook`, `is_session_busy`, `has_active_run`, `active_session_ids`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`import time`。
- 模块级配置或常量名称：`DEFAULT_EXECUTION_TIMEOUT_SECONDS`, `DEFAULT_USER_PREEMPTION_TIMEOUT_SECONDS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/execution.py#L1-L770)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/heartbeat/models.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=66aed36e9a75a7e2d33a6fd48ea72f72be530c5ed485902f0213a4823c6d2583 -->
**`jiuwenswarm/agents/harness/code/rails/heartbeat/models.py`**

- 源码对模块职责的说明：新 Heartbeat 任务数据模型 — 绑定当前会话的自动续跑触发器.。
- 调用入口 `validate_metadata_source(raw)`；声明返回 `str`。
- `HeartbeatSchedule` 定义类型边界；方法入口：`to_dict`, `from_dict`, `validate`。
- `HeartbeatRunState` 定义类型边界；方法入口：`to_dict`, `from_dict`。
- `HeartbeatJob` 定义类型边界；方法入口：`to_dict`, `from_dict`, `check_invariants`, `source`, `is_terminal`, `is_schedulable`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass, field`；`from typing import Any`；`from .cron_schedule import validate_cron_expression`。
- 模块级配置或常量名称：`HEARTBEAT_KIND`, `STATUS_SCHEDULED`, `STATUS_RUNNING`, `STATUS_COMPLETED`, `STATUS_EXPIRED`, `STATUS_DISABLED`, `HEARTBEAT_STATUSES`, `HEARTBEAT_TERMINAL_STATUSES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/models.py#L1-L593)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/heartbeat/runtime.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=65d2a35ce795b649a6608dfbb0acc0739ff4133489fc3f48cc390e4adc1c3969 -->
**`jiuwenswarm/agents/harness/code/rails/heartbeat/runtime.py`**

- 源码对模块职责的说明：Process-level owner for the Heartbeat Rail domain.。
- `HeartbeatRuntimeUnavailableError` 继承 `RuntimeError`。
- `HeartbeatRailRuntime` 定义类型边界；方法入口：`__init__`, `is_available`, `should_retain_session`, `start`, `stop`, `retain_agent`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/runtime.py#L1-L392)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dd120db5481af608270dde7984c5f4504a809202e7042ecbe53d9ac6aa9e3914 -->
**`jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py`**

- 源码对模块职责的说明：HeartbeatSchedulerService — 心跳任务后台调度.。
- `HeartbeatExecution` 继承 `Protocol`；方法入口：`is_session_busy`, `has_active_run`, `dispatch`, `cancel`。
- `HeartbeatSchedulerService` 定义类型边界；方法入口：`__init__`, `set_limits`, `suspend_session`, `resume_session`, `is_running`, `start`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`import secrets`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/scheduler.py#L1-L980)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/rails/heartbeat/session_resolver.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9c254edfe21f1976acfaa53995d5a886bd909a51acaecb285021f0cd48935b03 -->
**`jiuwenswarm/agents/harness/code/rails/heartbeat/session_resolver.py`**

- 源码对模块职责的说明：HeartbeatSessionResolver — 会话存在性检查与会话删除通知.。
- `SessionSummary` 定义类型边界。
- `HeartbeatSessionResolver` 定义类型边界；方法入口：`__init__`, `set_scheduler`, `resolve`, `on_session_deleted`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`from dataclasses import dataclass`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/rails/heartbeat/session_resolver.py#L1-L160)。
<!-- /kb:file -->
