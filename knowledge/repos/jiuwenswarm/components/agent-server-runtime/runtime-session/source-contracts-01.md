---
title: "runtime-session 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# runtime-session 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/runtime/session/git_diff_status.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c97dbc4eb8d50c67fa41ae46bd8548d722b007933dead535ade00e9d62312c60 -->
**`jiuwenswarm/server/runtime/session/git_diff_status.py`**

- 源码对模块职责的说明：DiffStatusService: 面向 Web 的 diff 状态聚合服务(设计文档 §2.4 / §3.5 / §4.1.16)。。
- `DiffStats` 定义类型边界；方法入口：`to_dict`。
- `DiffHunk` 定义类型边界；方法入口：`to_dict`。
- `DiffFileEntry` 定义类型边界；方法入口：`to_dict`。
- `DiffSummary` 定义类型边界；方法入口：`to_dict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import os`；`import re`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/git_diff_status.py#L1-L1064)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/session/git_diff_watcher.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2a6d11bb5f690ef2e162c3a17b56a0dc547e03c596ba72bc3fb95a1d00072b5f -->
**`jiuwenswarm/server/runtime/session/git_diff_watcher.py`**

- 源码对模块职责的说明：GitDiffWatcherRegistry: diff 实时监控核心逻辑(设计文档 §2.5 / §3.6 / §4.2)。。
- `GitDiffWatch` 定义类型边界。
- `GitDiffFilesState` 定义类型边界。
- `GitDiffDetailState` 定义类型边界。
- `GitDiffWatcherRegistry` 定义类型边界；方法入口：`__init__`, `set_channel`, `set_diff_status_fetcher`, `add_watch`, `remove_watch`, `update_files`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import hashlib`；`import logging`。
- 模块级配置或常量名称：`POLL_INTERVAL_SEC`, `DEBOUNCE_SEC`, `ERROR_BACKOFF_SEC`, `MAX_PUSH_FAILURES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/git_diff_watcher.py#L1-L1483)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/session/history_io.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc18fa0f68bf46f1c5fc3fc5d4b13556fe13ff13203657c3f7ffff7a7e2b00c5 -->
**`jiuwenswarm/server/runtime/session/history_io.py`**

- 源码对模块职责的说明：Async boundary for synchronous history persistence and queue backpressure.。
- 异步入口 `run_history_io(fn, *args, **kwargs)`；声明返回 `Any`。
- 调用入口 `stream_chunk_writes_history(chunk)`；声明返回 `bool`。
- 异步入口 `run_stream_parser(parser, chunk, **kwargs)`；声明返回 `Any`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`from typing import Any, Callable`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/history_io.py#L1-L42)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/session/kv_cache/kv_cache_application_owner.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b062cb4ce5e32d8ecf9263685f7a90be5a729b1a987db73f2339c7bd0004bd17 -->
**`jiuwenswarm/server/runtime/session/kv_cache/kv_cache_application_owner.py`**

- 源码对模块职责的说明：Application-scoped ownership and publication of KVC lifecycle resources.。
- `KVCacheApplicationState` 继承 `str, Enum`。
- `KVCacheApplicationOwner` 定义类型边界；方法入口：`__init__`, `state`, `closed`, `attach_runtime`, `activate_from_config`, `set_enabled`。
- 调用入口 `get_kv_cache_application_owner()`；声明返回 `KVCacheApplicationOwner`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`from collections.abc import Awaitable, Callable`；`from enum import Enum`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/kv_cache/kv_cache_application_owner.py#L1-L235)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/session/kv_cache/kv_cache_application_runtime.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=02ba3545017875aff0a6e545bdfdf4ca74e78d7396e2af2b4dad01349de3896c -->
**`jiuwenswarm/server/runtime/session/kv_cache/kv_cache_application_runtime.py`**

- 源码对模块职责的说明：Application ownership for the process-local Agent-Core KVC runtime.。
- 调用入口 `get_kv_cache_runtime()`；声明返回 `KVCacheRuntime / None`。
- 异步入口 `close_kv_cache_runtime()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from openjiuwen.core.kv_cache.kv_cache_config import KVC_TERMINAL_CLEANUP_T`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/kv_cache/kv_cache_application_runtime.py#L1-L90)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/session/kv_cache/kv_cache_model_provider.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=40e48585360eadbb0611ff9fc2cfd311a46e052e1f2b9af13bd4c15a8e67ff57 -->
**`jiuwenswarm/server/runtime/session/kv_cache/kv_cache_model_provider.py`**

- 源码对模块职责的说明：JiuwenSwarm configuration bridge for the shared KVC runtime.。
- 调用入口 `is_kv_cache_affinity_enabled(config)`；声明返回 `bool`。
- 调用入口 `create_default_kv_cache_model()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`；`from jiuwenswarm.common.config import get_config, get_default_models`；`from jiuwenswarm.common.kv_cache_affinity_config import has_kv_cache_affini`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/kv_cache/kv_cache_model_provider.py#L1-L84)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/session/kv_cache/kv_cache_session_lifecycle_participant.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=77a4b72df1db22ccb7aa3c763aa491f12ce5ac61ca0d542e6166a8027d0e1c84 -->
**`jiuwenswarm/server/runtime/session/kv_cache/kv_cache_session_lifecycle_participant.py`**

- 源码对模块职责的说明：KVC product implementation of Runtime-owned Session lifecycle protocols.。
- `KVCacheSessionLifecycleParticipant` 定义类型边界；方法入口：`__init__`, `name`, `before_delete`, `release_resources`, `delete_failed`, `delete_committed`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from openjiuwen.core.kv_cache.kv_cache_config import KVC_TERMINAL_CLEANUP_T`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/kv_cache/kv_cache_session_lifecycle_participant.py#L1-L218)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/session/kv_cache/kv_cache_task_guard.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cc142144323168093120a2c355dc44d060d83729832427a6e0ab707e0ebf515d -->
**`jiuwenswarm/server/runtime/session/kv_cache/kv_cache_task_guard.py`**

- 源码对模块职责的说明：Lightweight, process-local product Session facts for KVC lifecycle.。
- `KVCGuardActionRequest` 定义类型边界。
- `SessionKVCFacts` 定义类型边界。
- `SessionKVCacheTaskGuard` 定义类型边界；方法入口：`__init__`, `forget`, `snapshot`, `set_foreground`, `prepare`, `task_started`。
- 调用入口 `get_session_kv_cache_task_guard()`；声明返回 `SessionKVCacheTaskGuard`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass, field`；`from typing import Literal`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/kv_cache/kv_cache_task_guard.py#L1-L208)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/session/model_selection_store.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=014443c79a46c7443ff1fd1568049bcf67bd045b2f7a00fb946d54c4f10e352e -->
**`jiuwenswarm/server/runtime/session/model_selection_store.py`**

- 源码对模块职责的说明：Safe persistence for stable per-session model selections.。
- 调用入口 `get_session_model_selection(session_id)`；声明返回 `ModelSelection / None`。
- 调用入口 `set_session_model_selection(session_id, selection)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import os`；`import re`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/model_selection_store.py#L1-L54)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/session/project_git.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c58e556bab06567ce39da1487a9c4c740478e06268cb07f8d4e83ed7b87b1b87 -->
**`jiuwenswarm/server/runtime/session/project_git.py`**

- 源码对模块职责的说明：ProjectGitService: 项目目录的 Git 仓库探测与分支操作服务(设计文档 §3.4 / §6)。。
- `GitError` 定义类型边界；方法入口：`to_dict`。
- `GitRepoStatus` 定义类型边界；方法入口：`to_dict`。
- `GitProbeResult` 定义类型边界；方法入口：`to_dict`。
- `GitOperationResult` 定义类型边界；方法入口：`to_dict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import os`；`import subprocess`。
- 模块级配置或常量名称：`GIT_COMMAND_TIMEOUT_SEC`, `GIT_DIFF_TIMEOUT_SEC`, `GIT_PUSH_TIMEOUT_SEC`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/project_git.py#L1-L2206)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/session/project_queries.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8dde715806c2ffd49c592cdd0c5f853ca4824991386d0d378df11444571a5bf6 -->
**`jiuwenswarm/server/runtime/session/project_queries.py`**

- 源码对模块职责的说明：Compatibility shim. Disk project queries live in Control store.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.control.store.project_queries import attribute_sess`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/project_queries.py#L1-L25)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/session/project_store.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7ec83ef233556d8c94116894d2952ca58ddd367a60dcfeffe316d0ba93d46ff4 -->
**`jiuwenswarm/server/runtime/session/project_store.py`**

- 源码对模块职责的说明：项目存储模块 — projects.json 的持久化与 CRUD。。
- 调用入口 `file_lock(data_path)`；声明返回 `Iterator[None]`。
- `Project` 定义类型边界；方法入口：`to_dict`, `from_dict`。
- `CronProjectBinding` 定义类型边界。
- 调用入口 `get_project_by_id(project_id, cache_bust)`；声明返回 `Project / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/project_store.py#L1-L1113)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/session/session_archive.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3ea69911d97fd10ffc8381cf651f60a57b17e92b96873f8f37205f535a4de5a9 -->
**`jiuwenswarm/server/runtime/session/session_archive.py`**

- 源码对模块职责的说明：Archive operations owned by the AgentServer runtime, never Gateway fallback.。
- 调用入口 `get_agent_sessions_dir()`。
- `ProjectSessionInventoryItem` 定义类型边界。
- `SessionArchiveService` 定义类型边界；方法入口：`__init__`, `lock`, `start_recovery`, `close`, `stop`, `session`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import os`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/session/session_archive.py#L1-L1250)。
<!-- /kb:file -->
