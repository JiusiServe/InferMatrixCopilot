---
title: "team-handlers 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# team-handlers 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/team/handlers/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=996a1ae7486d2e9af1aaae5f2bce225b5be957bb17d8a33b6347168735214baf -->
**`jiuwenswarm/agents/harness/team/handlers/__init__.py`**

- 源码对模块职责的说明：Team event handlers — monitor and workflow status.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.agents.harness.team.handlers.team_monitor_handler import T`；`from jiuwenswarm.agents.harness.team.handlers.workflow_monitor_handler impo`；`from jiuwenswarm.agents.harness.team.handlers.workflow_state import Workflo`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/__init__.py#L1-L23)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/team/handlers/base_monitor_handler.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f2326965a386da327d919c65fbc1fcd93dcd95f4aa0ab88535e0475bd22bd655 -->
**`jiuwenswarm/agents/harness/team/handlers/base_monitor_handler.py`**

- 源码对模块职责的说明：Base class for TeamMonitor-backed event handlers.。
- `DropOldestQueue` 继承 `asyncio.Queue`；方法入口：`__init__`, `put_nowait`, `put`。
- `BaseMonitorHandler` 定义类型边界；方法入口：`__init__`, `session_id`, `is_running`, `set_consumer_task`, `start`, `stop`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from typing import Any, AsyncIterator, Optional`。
- 模块级配置或常量名称：`MONITOR_EVENT_QUEUE_MAXSIZE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/base_monitor_handler.py#L1-L238)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/team/handlers/team_monitor_handler.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a5cc4bc31742445ec68733a585b51823e162a9717e845cb4ba9d84603be8a85a -->
**`jiuwenswarm/agents/harness/team/handlers/team_monitor_handler.py`**

- 源码对模块职责的说明：Team Monitor 处理器.。
- `TeamMonitorHandler` 继承 `BaseMonitorHandler`；方法入口：`__init__`, `team_id`, `get_team_snapshot`, `get_member_list`, `get_member_list_from_db`, `get_team_snapshot_from_db`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/team_monitor_handler.py#L1-L656)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ddedd8fbdaa38e960cd85e34e753179b11221242fcd8097bc6174b8d6a3a0b12 -->
**`jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py`**

- 源码对模块职责的说明：Workflow Monitor Handler — bridges WorkflowProgressTeamEvent to workflow.updated events.。
- `WorkflowMonitorHandler` 继承 `BaseMonitorHandler`；方法入口：`__init__`, `channel_id`, `get_workflow_snapshot`, `finalize_pending_runs`, `get_run_states`, `stop_run`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Any, Literal, Optional`；`from openjiuwen.agent_teams.monitor.team_monitor import TeamMonitor`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py#L1-L343)。
<!-- /kb:file -->
