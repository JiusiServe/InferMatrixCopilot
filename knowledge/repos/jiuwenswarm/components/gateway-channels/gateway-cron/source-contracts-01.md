---
title: "gateway-cron 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# gateway-cron 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/gateway/cron/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5df58b6ba727f1fa079ca46c9f92cae904a15e44c2040eb244be74aa458b3818 -->
**`jiuwenswarm/gateway/cron/__init__.py`**

- 源码对模块职责的说明：Cron job scheduling for Gateway.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .controller import CronController`；`from .factory import create_gateway_cron_store`；`from .models import CronJob, CronTarget, CronTargetChannel`；`from .scheduler import CronSchedulerService`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/cron/__init__.py#L1-L26)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/cron/controller.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f5d615472c3c387c39df221a9a85e603d206c91b0a349c17a48eafc991f2ee9f -->
**`jiuwenswarm/gateway/cron/controller.py`**

- `CronController` 定义类型边界；方法入口：`__init__`, `store`, `scheduler`, `set_target_channel`, `get_instance`, `reset_instance`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from functools import wraps`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/cron/controller.py#L1-L939)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/cron/cron_expr.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e81cacfb477d17fc12e7457084355e05531bb32a644e5fa666c35b466adb8831 -->
**`jiuwenswarm/gateway/cron/cron_expr.py`**

- 源码对模块职责的说明：Compatibility alias for cron expressions now owned by Agent Runtime.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import sys`；`from jiuwenswarm.runtime.cron import cron_expr as _implementation`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/cron/cron_expr.py#L1-L7)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/cron/cron_json_convert.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8c399f723e9931aba71f693cfc2ce63e40fc3a8f80fdaf2d08c67590c1e32c36 -->
**`jiuwenswarm/gateway/cron/cron_json_convert.py`**

- 源码对模块职责的说明：CLI 工具：把 cron JSON 在「扁平结构」与「OpenClaw 嵌套结构」之间互转。。
- 调用入口 `convert_cron_job_dict_to_flat(data)`；声明返回 `dict[str, Any]`。
- 调用入口 `convert_flat_cron_job_to_openclaw_dict(flat_job)`；声明返回 `dict[str, Any]`。
- 调用入口 `convert_file(input_path, output_path, to_format)`；声明返回 `None`。
- 调用入口 `main(argv)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import sys`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/cron/cron_json_convert.py#L1-L264)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/cron/dingtalk_routing.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=71a9a682091a6089e66c41bf69b91ae1eddd4616f40abf025dbc952d78106458 -->
**`jiuwenswarm/gateway/cron/dingtalk_routing.py`**

- 源码对模块职责的说明：Compatibility alias for transport-neutral DingTalk cron bindings.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import sys`；`from jiuwenswarm.runtime.cron import dingtalk_routing as _implementation`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/cron/dingtalk_routing.py#L1-L7)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/cron/factory.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f71fb48c887bd4935f64b514b01ddcde8d44f504ca4b46dd0759a756046b3dfd -->
**`jiuwenswarm/gateway/cron/factory.py`**

- 源码对模块职责的说明：Compatibility alias for the cron store factory now owned by Agent Runtime.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import sys`；`from jiuwenswarm.runtime.cron import factory as _implementation`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/cron/factory.py#L1-L7)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/cron/lifecycle_owners.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c47bf12615f8ccbd9a079c80ec289637365ad127eb3de7f33ef3325fa9514233 -->
**`jiuwenswarm/gateway/cron/lifecycle_owners.py`**

- 源码对模块职责的说明：Durable routing identities for project lifecycle recovery.。
- `LifecycleOwners` 定义类型边界；方法入口：`__init__`, `read`, `remember`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import os`；`import uuid`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/cron/lifecycle_owners.py#L1-L47)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/cron/proactive_cron_sync.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0be5683b5b2ec644b34db2f8d4afdb5960f0911d59d87628ee7c0f6b9b59a251 -->
**`jiuwenswarm/gateway/cron/proactive_cron_sync.py`**

- 源码对模块职责的说明：Auto-register the proactive-recommendation tick cron job.。
- 异步入口 `sync_proactive_tick_job(cron_controller, config_payload)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Any`。
- 模块级配置或常量名称：`PROACTIVE_JOB_ID`, `PROACTIVE_JOB_NAME`, `DEFAULT_CRON_EXPR`, `DEFAULT_TARGET_CHANNEL`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/cron/proactive_cron_sync.py#L1-L135)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/cron/scheduler.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0270e3a8507383f62d21beac395777603080e2237aa711c0a1c075dc78d2f9e0 -->
**`jiuwenswarm/gateway/cron/scheduler.py`**

- `CronSchedulerService` 定义类型边界；方法入口：`__init__`, `is_running`, `start`, `stop`, `reload`, `remember_lifecycle_owner`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import heapq`；`import json`。
- 模块级配置或常量名称：`CRON_INTERRUPT_EVENT_TYPES`, `CRON_INTERRUPT_RESULT_TEXT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/cron/scheduler.py#L1-L2445)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/cron/store.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b564b6f32c9086b94bd50e5b83aec526627c1a04c89676b5e7b0e5f1caf1a4b7 -->
**`jiuwenswarm/gateway/cron/store.py`**

- 源码对模块职责的说明：Compatibility alias for cron persistence now owned by Agent Runtime.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import sys`；`from jiuwenswarm.runtime.cron import store as _implementation`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/cron/store.py#L1-L7)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/cron/store_base.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=381828226f3f34860d40c71280d326eabdf99b3289bfadf669ef5ebd45ca2dc1 -->
**`jiuwenswarm/gateway/cron/store_base.py`**

- 源码对模块职责的说明：Compatibility alias for cron store backend protocol now owned by Agent Runtime.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import sys`；`from jiuwenswarm.runtime.cron import store_base as _implementation`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/cron/store_base.py#L1-L7)。
<!-- /kb:file -->
