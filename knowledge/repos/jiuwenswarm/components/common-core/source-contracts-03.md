---
title: "common-core 源码接口与集成边界 03"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-core 源码接口与集成边界 03

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/common/stage_timer.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c9374eae7d58bb7c012ba16882af26efeec2df51d0b5f4353c8eb6788a1d065c -->
**`jiuwenswarm/common/stage_timer.py`**

- 源码对模块职责的说明：Per-stage timing for a linear sequence of steps on a hot path.。
- `StageTimer` 定义类型边界；方法入口：`__init__`, `mark`, `total_ms`, `render`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from time import monotonic`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/stage_timer.py#L1-L72)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/startup_diagnostics.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=82c408a4065701d16c1bbf2f16c6081e36fc9a95185347ee51ac1724787be1fd -->
**`jiuwenswarm/common/startup_diagnostics.py`**

- 源码对模块职责的说明：Early, stdlib-only diagnostics for frozen desktop startup failures.。
- 调用入口 `default_doctor_output_path()`；声明返回 `Path`。
- 调用入口 `run_doctor(import_module, platform_name, windows_dll_loader)`；声明返回 `dict[str, Any]`。
- 调用入口 `summarize_doctor_result(result)`；声明返回 `str`。
- 调用入口 `write_doctor_result(path, result)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import importlib`；`import json`。
- 模块级配置或常量名称：`DOCTOR_FLAG`, `DOCTOR_WORKER_FLAG`, `DOCTOR_OUTPUT_FLAG`, `DOCTOR_SUMMARY_OUTPUT_FLAG`, `DOCTOR_TIMEOUT_SECONDS`, `DOCTOR_EXIT_OK`, `DOCTOR_EXIT_ENVIRONMENT_ERROR`, `DOCTOR_EXIT_INTERNAL_ERROR`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/startup_diagnostics.py#L1-L583)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/task_loop_config.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c765b1516db5fc05dbc32c858fcd6188eb7d37ef2927aacbd9a3c52a725c2eec -->
**`jiuwenswarm/common/task_loop_config.py`**

- 源码对模块职责的说明：Task-loop configuration helpers.。
- 调用入口 `resolve_task_loop_completion_timeout(config)`；声明返回 `float / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import math`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/task_loop_config.py#L1-L26)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/team_artifacts.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f533fe45aa8f91db5b7dd7100ff94046bd01bbeeb9239249522a5eb997a80259 -->
**`jiuwenswarm/common/team_artifacts.py`**

- 源码对模块职责的说明：Team-scoped final-deliverables and per-member work directories.。
- `TeamArtifactWorkspace` 定义类型边界。
- 调用入口 `get_team_artifacts_dir(team_ws_root)`；声明返回 `Path`。
- 调用入口 `get_team_artifact_workspace(team_ws_root, session_id, task_name)`；声明返回 `TeamArtifactWorkspace`。
- 调用入口 `resolve_member_work_dir(root_dir, member_name)`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`from dataclasses import dataclass`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/team_artifacts.py#L1-L144)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/todo_snapshot.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7e2a61c6ea5c378ea4c9096b1e8bfd995b5772a7e9d07f3461c335ca1d4651ac -->
**`jiuwenswarm/common/todo_snapshot.py`**

- 源码对模块职责的说明：Todo workspace snapshot helpers for frontend restore.。
- 调用入口 `format_todos_for_frontend(todos_data)`；声明返回 `list[dict[str, Any]]`。
- 调用入口 `session_uses_project_todo_dir(project_dir, work_mode, mode)`；声明返回 `bool`。
- 调用入口 `todo_snapshot_candidate_paths(session_id, project_dir, work_mode, mode)`；声明返回 `list[Path]`。
- 调用入口 `load_todo_snapshot_for_frontend(session_id, project_dir, work_mode, mode)`；声明返回 `list[dict[str, Any]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from pathlib import Path`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/todo_snapshot.py#L1-L202)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/tool_display.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=654af20e96f46a7cc504adf8bd12ac877c8b57369acc99e97c85eb03a62f9216 -->
**`jiuwenswarm/common/tool_display.py`**

- 源码对模块职责的说明：工具调用展示辅助：call_goal schema 注入与参数剥离。。
- 调用入口 `inject_call_goal_schema(parameters)`；声明返回 `None`。
- 调用入口 `extract_call_goal(arguments)`；声明返回 `tuple[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from typing import Any, Mapping`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/tool_display.py#L1-L87)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/tool_ownership.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=741c4226f66c811dfecd8a577ed6efd7604cc79c42311f5b91b6532607ed3afb -->
**`jiuwenswarm/common/tool_ownership.py`**

- 源码对模块职责的说明：Single source of truth for how a tool instance is registered process-wide.。
- 调用入口 `mark_stateless(tools)`；声明返回 `list[Any]`。
- 调用入口 `qualify_tool_id(card, owner_id)`；声明返回 `str`。
- 调用入口 `register_tool(tool, owner_id)`；声明返回 `None`。
- 调用入口 `unregister_tool(tool)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from openjiuwen.core.foundation.tool import ToolCard`；`from openjiuwen.core.runner import Runner`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/tool_ownership.py#L1-L112)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/updater.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a327e377615b934e2d5fa10cd915339daf5b254b96e0661140528e8f813231e3 -->
**`jiuwenswarm/common/updater.py`**

- 调用入口 `get_access_token()`；声明返回 `str`。
- `UpdateStatus` 定义类型边界。
- `UpdaterService` 定义类型边界；方法入口：`__init__`, `get_status`, `get_runtime_config`, `check`, `start_download`, `start_upgrade`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import signal`；`import sys`。
- 模块级配置或常量名称：`DEFAULT_RELEASE_API_GITCODE`, `DEFAULT_RELEASE_API_GITHUB`, `DEFAULT_RELEASE_API_PYPI`, `DEFAULT_ASSET_PATTERN_LINUX`, `DEFAULT_TIMEOUT_SECONDS`, `DEFAULT_TEXT`, `DESKTOP_ENV_FLAG`, `DESKTOP_INSTALLER_SUFFIXES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/updater.py#L1-L572)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/updater_restart_helper.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8d25f9a14fdf94f4a39f3e1036fb82a3caec96ce930fc9ea3e5df619e00d9e71 -->
**`jiuwenswarm/common/updater_restart_helper.py`**

- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/updater_restart_helper.py#L1-L128)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/upgrade_executor.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ec99b07e09d219fded1b740d8c494c795a6b2939fa187a3b2b502d11959bb51b -->
**`jiuwenswarm/common/upgrade_executor.py`**

- 调用入口 `restart_pending_path()`；声明返回 `Path`。
- `UpgradeExecutor` 继承 `ABC`；方法入口：`__init__`, `install`, `upgrade`。
- `DesktopExecutor` 继承 `UpgradeExecutor`；方法入口：`__init__`, `install`。
- `PipExecutor` 继承 `UpgradeExecutor`；方法入口：`__init__`, `install`, `upgrade`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import os`；`import shutil`。
- 模块级配置或常量名称：`DOWNLOAD_CHUNK_SIZE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/upgrade_executor.py#L1-L439)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/utils.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aebb9157ed790107293506971e558db0b4c926609235828798a17112d366d350 -->
**`jiuwenswarm/common/utils.py`**

- 源码对模块职责的说明：Path management for JiuWenSwarm.。
- `CopyDiffResult` 定义类型边界。
- `TrackCopyDiff` 定义类型边界；方法入口：`__init__`。
- `LoggingLevels` 定义类型边界。
- `SafeRotatingFileHandler` 继承 `BaseRotatingHandler`；方法入口：`__init__`, `shouldRollover`, `doRollover`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import ctypes`；`import hashlib`；`import json`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/utils.py#L1-L3031)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/version.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=58491de7fc9f02e6cc937a514597d7be6dc34ca532ecc6e6760265beb812f3b5 -->
**`jiuwenswarm/common/version.py`**

- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.common._build_config import VERSION`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/version.py#L1-L6)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/version_source.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fefc1f7198ec8609d2c27e8faab646f6292f48b3d2750d30570dcf7ac43c98dc -->
**`jiuwenswarm/common/version_source.py`**

- 调用入口 `is_prerelease_version(version)`；声明返回 `bool`。
- 调用入口 `strip_prerelease_suffix(version)`；声明返回 `str`。
- 调用入口 `release_sort_key(version)`；声明返回 `tuple[tuple[int, ...], int, tuple[int, ...]]`。
- 调用入口 `release_timestamp_key(value)`；声明返回 `datetime`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import re`。
- 模块级配置或常量名称：`DEFAULT_TIMEOUT_SECONDS`, `RELEASES_PER_PAGE`, `MAX_RELEASE_PAGES`, `GITHUB_API`, `GITCODE_API`, `PYPI_SIMPLE_API`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/version_source.py#L1-L640)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/work_mode.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c71d76ed0869bb7c1ed0ee03eded6791a29a5aeb0ea20481719e2d48fcc0765d -->
**`jiuwenswarm/common/work_mode.py`**

- 源码对模块职责的说明：工作模式（work_mode）共享基础设施。。
- 调用入口 `normalize_work_mode(raw, default)`；声明返回 `str`。
- 调用入口 `is_default_project_id(project_id)`；声明返回 `bool`。
- 调用入口 `resolve_default_project_id(work_mode)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`。
- 模块级配置或常量名称：`DEFAULT_WEB_WORK_MODE`, `DEFAULT_TUI_WORK_MODE`, `SUPPORTED_WORK_MODES`, `DEFAULT_PROJECT_ID_WORK`, `DEFAULT_PROJECT_ID_CODE`, `DEFAULT_PROJECT_IDS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/work_mode.py#L1-L51)。
<!-- /kb:file -->
