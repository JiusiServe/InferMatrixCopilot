---
title: "advanced-daily-report-collectors 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# advanced-daily-report-collectors 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=327adb8f3816de4555e7f9bdbee7099e4d954cbdd23d0266f7258a5d9b4e213d -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/__init__.py`**

- 源码对模块职责的说明：进阶版日报生成器 - 数据采集模块。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .git_collector import GitCollector, GitCommit`；`from .email_collector import EmailCollector, EmailStats`；`from .memory_collector import MemoryCollector`；`from .todo_collector import TodoCollector`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/__init__.py#L1-L28)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/aggregator.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=565ceab6981f01ba5d240781ca330b62fdcb9658cc29720b58baa76631754147 -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/aggregator.py`**

- 源码对模块职责的说明：数据聚合器。
- `CollectedData` 定义类型边界；方法入口：`to_dict`, `to_json`。
- `DataAggregator` 定义类型边界；方法入口：`__init__`, `collect`, `collect_week`, `collect_month`, `collect_for_pattern_analysis`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import json`；`import logging`；`from dataclasses import dataclass, field`；`from datetime import datetime, timedelta`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/aggregator.py#L1-L244)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/email_collector.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7c01eae777c3c32efc782e3ab92fadc1017bc5fba4a94058cb4aff59af641dec -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/email_collector.py`**

- 源码对模块职责的说明：邮件统计采集器。
- `EmailInfo` 定义类型边界；方法入口：`to_dict`。
- `EmailStats` 定义类型边界；方法入口：`to_dict`。
- `EmailCollector` 定义类型边界；方法入口：`__init__`, `connect`, `disconnect`, `get_stats`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import email`；`import logging`；`from dataclasses import dataclass, field`；`from datetime import datetime`。
- 模块级配置或常量名称：`NETEASE_IMAP_SERVERS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/email_collector.py#L1-L276)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/git_collector.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=be03713c81e7652d36e1ffe696a2dcf697725419a3d5457c869ad82049566637 -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/git_collector.py`**

- 源码对模块职责的说明：Git 提交记录采集器。
- `GitCommit` 定义类型边界；方法入口：`to_dict`。
- `GitStats` 定义类型边界；方法入口：`net_lines`, `to_dict`。
- `GitCollector` 定义类型边界；方法入口：`__init__`, `get_commits`, `get_week_commits`, `get_month_commits`, `get_commits_for_pattern_analysis`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import subprocess`；`from dataclasses import dataclass, field`；`from datetime import datetime, timedelta`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/git_collector.py#L1-L272)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/memory_collector.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=06f6a5e8083895066c717c52c61af3ddb98ec1fb1a9c07fdb7715f94538d80ff -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/memory_collector.py`**

- 源码对模块职责的说明：记忆数据采集器。
- `MemoryData` 定义类型边界；方法入口：`to_dict`。
- `MemoryCollector` 定义类型边界；方法入口：`__init__`, `collect`, `get_week_memories`, `get_month_memories`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import re`；`from dataclasses import dataclass, field`；`from datetime import datetime, timedelta`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/memory_collector.py#L1-L157)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/todo_collector.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7c2023d127d588876cbe43185d32f0e96f14561278abda5b6891815d32cf9d14 -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/todo_collector.py`**

- 源码对模块职责的说明：待办事项采集器。
- `TodoTask` 定义类型边界；方法入口：`to_dict`。
- `TodoStats` 定义类型边界；方法入口：`completion_rate`, `to_dict`。
- `TodoCollector` 定义类型边界；方法入口：`__init__`, `collect`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import re`；`from dataclasses import dataclass, field`；`from datetime import datetime`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/todo_collector.py#L1-L226)。
<!-- /kb:file -->
