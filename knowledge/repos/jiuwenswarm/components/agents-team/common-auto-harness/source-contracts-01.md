---
title: "common-auto-harness 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-auto-harness 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=06198195a7057e47960970133f607760997a0ac9744cf9809128b28e50e5b972 -->
**`jiuwenswarm/agents/harness/common/auto_harness/__init__.py`**

- 源码对模块职责的说明：Auto-Harness module: single execution and scheduled task management.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .service import AutoHarnessService, ActiveAutoHarnessRun, reset_harnes`；`from .scheduler import Scheduler`；`from .task_store import TaskStore`；`from .config_validator import ConfigValidator`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/__init__.py#L1-L28)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/capabilities.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1672cf451d2900b908feabc7ae96828b93e543335e4b981cf28b9c3bbfe32b4c -->
**`jiuwenswarm/agents/harness/common/auto_harness/capabilities.py`**

- 源码对模块职责的说明：Capability registry for auto-harness scenario extensions.。
- `AutoHarnessCapability` 继承 `Protocol`；方法入口：`handle`。
- `AutoHarnessCapabilityRegistry` 定义类型边界；方法入口：`__init__`, `register`, `handle`。
- 调用入口 `create_default_capability_registry(data_dir, task_store, harness_service, base_config_getter, default_repo_url)`；声明返回 `AutoHarnessCapabilityRegistry`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from pathlib import Path`；`from typing import Any, Callable, Optional, Protocol`；`from openjiuwen.core.foundation.llm import Model`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/capabilities.py#L1-L84)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/config_validator.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=72b7ed74b60217a1f596b3eadebba29ed3de491b326272126d163c0611539699 -->
**`jiuwenswarm/agents/harness/common/auto_harness/config_validator.py`**

- 源码对模块职责的说明：Configuration validator for scheduled auto_harness tasks.。
- `ConfigValidator` 定义类型边界；方法入口：`__init__`, `check_config`, `update_config`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import os`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/config_validator.py#L1-L177)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/issue_fix/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=39c6ecc2b06bf57d07ad5538dd1900a799bb637aa4aef2e711eb98f3582a7f97 -->
**`jiuwenswarm/agents/harness/common/auto_harness/issue_fix/__init__.py`**

- 源码对模块职责的说明：Issue-fix integration for auto-harness.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .gitcode_issue_client import GitCodeIssue, GitCodeIssueClient`；`from .issue_runner import GitCodeIssueRunner, IssueWatchOptions`；`from .issue_state_store import IssueStateStore`；`from .service import IssueFixService`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/issue_fix/__init__.py#L1-L19)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/issue_fix/code_rules.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=143489a1a33bd7ce778d3c7deefa93e67c18fd02912a4c5725b492b10b31c263 -->
**`jiuwenswarm/agents/harness/common/auto_harness/issue_fix/code_rules.py`**

- 源码对模块职责的说明：Code rule loading for GitCode issue-fix tasks.。
- 调用入口 `load_code_rules()`；声明返回 `str`。
- 调用入口 `format_code_rules_prompt()`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from functools import lru_cache`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/issue_fix/code_rules.py#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/issue_fix/gitcode_issue_client.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d18ea34c52c0789bcf8f7528edc990f91fcca7c3ff4859674e28ae44d51d81fc -->
**`jiuwenswarm/agents/harness/common/auto_harness/issue_fix/gitcode_issue_client.py`**

- 源码对模块职责的说明：Small GitCode API client for auto-harness issue ingestion.。
- `GitCodeIssue` 定义类型边界。
- `GitCodeIssueClient` 定义类型边界；方法入口：`__init__`, `list_issues`, `list_all_issues`, `get_issue`, `list_issue_pull_requests`, `list_pull_requests`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`import logging`；`from typing import Any, Optional`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/issue_fix/gitcode_issue_client.py#L1-L226)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/issue_fix/issue_matrix_store.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=be39999faeca4f9e6052df2c7b335e9d14003c68a824a742523d3d41ac137e01 -->
**`jiuwenswarm/agents/harness/common/auto_harness/issue_fix/issue_matrix_store.py`**

- 源码对模块职责的说明：Issue matrix storage for tracking analyzed GitCode issues.。
- `IssueMatrixStore` 定义类型边界；方法入口：`__init__`, `load`, `save`, `get_entry`, `remove_entry`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`from datetime import datetime, timezone`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/issue_fix/issue_matrix_store.py#L1-L106)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/issue_fix/issue_runner.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ecec5ec3cccdfd82f2f9f2e23bbd4145c72c2cea8078fa6a3a136e04f8f3298e -->
**`jiuwenswarm/agents/harness/common/auto_harness/issue_fix/issue_runner.py`**

- 源码对模块职责的说明：GitCode issue ingestion and auto-harness task orchestration.。
- `AutoHarnessTaskService` 继承 `Protocol`；方法入口：`run_task`, `get_scheduled_task_status`。
- `IssueWatchOptions` 定义类型边界。
- `GitCodeIssueRunner` 定义类型边界；方法入口：`__init__`, `build_issue_fix_query`, `assess_issue_difficulty`, `reconcile`, `process_issues_once`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`from dataclasses import dataclass`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/issue_fix/issue_runner.py#L1-L566)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/issue_fix/issue_state_store.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9396ccf54c6210019c9b56def950b7e148e94dab763f54551ed790ad7735b70a -->
**`jiuwenswarm/agents/harness/common/auto_harness/issue_fix/issue_state_store.py`**

- 源码对模块职责的说明：Persistent state for GitCode issue auto-harness runs.。
- `IssueStateStore` 定义类型边界；方法入口：`__init__`, `issue_key`, `get`, `list`, `update`, `delete`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`from datetime import datetime, timezone`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/issue_fix/issue_state_store.py#L1-L87)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/issue_fix/run_progress.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2681e4a2d4c0c75f27e9c0e880450976836d348935b2e0f2c17fbb2f26bed65e -->
**`jiuwenswarm/agents/harness/common/auto_harness/issue_fix/run_progress.py`**

- 源码对模块职责的说明：Issue-fix run-log status extensions.。
- 调用入口 `infer_issue_fix_skipped_stages(content)`；声明返回 `tuple[str, ...]`。
- 调用入口 `enrich_issue_fix_progress(progress, logs)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import re`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/issue_fix/run_progress.py#L1-L72)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/issue_fix/service.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c6cbaab3010dae8275a8d805e533f631d5e0409a6d331a76671d2f84eb7df940 -->
**`jiuwenswarm/agents/harness/common/auto_harness/issue_fix/service.py`**

- 源码对模块职责的说明：Issue-fix facade that keeps GitCode issue handling out of core service.。
- `IssueFixService` 定义类型边界；方法入口：`__init__`, `handle`, `process_gitcode_issues_once`, `list_gitcode_issue_states`, `delete_issue_states`, `refresh_issue_matrix`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`from pathlib import Path`；`from typing import Any, Callable, Optional`。
- 模块级配置或常量名称：`RUNNING_STATUSES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/issue_fix/service.py#L1-L534)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/issue_fix/task_factory.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b1c4d352d27a43527b786413a71d689520ef4aa4e34c3285243be3defe8f690b -->
**`jiuwenswarm/agents/harness/common/auto_harness/issue_fix/task_factory.py`**

- 源码对模块职责的说明：Task construction helpers for GitCode issue-fix runs.。
- 调用入口 `build_issue_fix_task(issue_number, query)`；声明返回 `OptimizationTask`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from openjiuwen.rsi.harness_rsi.auto_harness.schema import OptimizationTask`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/issue_fix/task_factory.py#L1-L17)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/repo_auth/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=20b6fbe76d890091dcf3b1aea9921825c7a68e471a9dc1c90bf5bee8eaefcf6d -->
**`jiuwenswarm/agents/harness/common/auto_harness/repo_auth/__init__.py`**

- 源码对模块职责的说明：Repository authentication helpers for auto-harness.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .gitcode import configure_gitcode_auth`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/repo_auth/__init__.py#L1-L7)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_harness/repo_auth/gitcode.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b13300fbd1766fd476465641151b6bf9eddbbcec4a28b3865171ac5563f34494 -->
**`jiuwenswarm/agents/harness/common/auto_harness/repo_auth/gitcode.py`**

- 源码对模块职责的说明：GitCode repository authentication helpers.。
- 异步入口 `configure_gitcode_auth(local_path, username, token, push_remote)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/repo_auth/gitcode.py#L1-L64)。
<!-- /kb:file -->
