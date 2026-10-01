---
title: "observability 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# observability 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/observability/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=da435b034577378775755faa145c1ad6c97e293131d61aa5264c8f8eeb7b65ed -->
**`jiuwenswarm/observability/__init__.py`**

- 源码对模块职责的说明：JiuwenSwarm persistence and delivery for OTLP trajectory records.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.observability.config import TrajectoryStoreSettings, load_`；`from jiuwenswarm.observability.models import CommittedTraceUpdate, OtlpSpan`；`from jiuwenswarm.observability.sink import TrajectoryRecordSink, Trajectory`；`from jiuwenswarm.observability.runtime import get_trajectory_runtime_sink, `。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/__init__.py#L1-L41)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/observability/config.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=def4efd44bd219d95edccde8067fd9ec21987680810a77ac03338676aa1dfac8 -->
**`jiuwenswarm/observability/config.py`**

- 源码对模块职责的说明：Configuration resolution for the local trajectory read store.。
- `TrajectoryStoreSettings` 定义类型边界。
- 调用入口 `session_database_path(database_root, session_id)`；声明返回 `Path`。
- 调用入口 `database_files(database_path)`；声明返回 `tuple[Path, Path, Path]`。
- 调用入口 `load_trajectory_store_settings(config, workspace)`；声明返回 `TrajectoryStoreSettings`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`from collections.abc import Mapping`；`from dataclasses import dataclass`。
- 模块级配置或常量名称：`DEFAULT_QUEUE_SIZE`, `DEFAULT_BATCH_SIZE`, `DEFAULT_FLUSH_INTERVAL_MS`, `DEFAULT_RETENTION_DAYS`, `DEFAULT_DETAIL_MAX_BYTES`, `DEFAULT_SESSION_DATABASE_DIRECTORY`, `DEFAULT_DISCARD_FINAL_SPAN_FRAMES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/config.py#L1-L165)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/observability/gateway_hints.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bef6dd6b142407066f6de99e5e7686f44b5db2748e6ab0b68406a68c3aa7ab7b -->
**`jiuwenswarm/observability/gateway_hints.py`**

- 源码对模块职责的说明：Cross-process delivery of committed trajectory revision hints.。
- `TrajectoryGatewayHintBridge` 定义类型边界；方法入口：`__init__`, `bind`, `unbind`, `publish`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`import threading`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/gateway_hints.py#L1-L167)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/observability/runtime.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2f65cfadbe7f048cec0515f231fa9e0addcaea1d526884ec12ce1890ee377afb -->
**`jiuwenswarm/observability/runtime.py`**

- 源码对模块职责的说明：AgentServer lifecycle for the Core OTLP record consumer.。
- 调用入口 `sync_trajectory_runtime(settings, on_commit, demand)`；声明返回 `TrajectorySessionSinkRouter / None`。
- 调用入口 `start_trajectory_runtime(settings, on_commit)`；声明返回 `TrajectorySessionSinkRouter / None`。
- 调用入口 `shutdown_trajectory_runtime(timeout, demand)`；声明返回 `bool`。
- 调用入口 `get_trajectory_runtime_sink()`；声明返回 `TrajectorySessionSinkRouter / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import threading`；`from typing import Protocol`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/runtime.py#L1-L222)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/observability/turn.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2344ff0f71c00db088b72c331d136f37e2d722ea9c47de84cc9b9e2a2b4dc25b -->
**`jiuwenswarm/observability/turn.py`**

- 源码对模块职责的说明：Trajectory turn identity for a session.。
- `TurnIdentity` 定义类型边界；方法入口：`to_dict`, `from_dict`。
- `SessionTurnTracker` 定义类型边界；方法入口：`__init__`, `current`, `resolve`, `sync`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import uuid`；`from dataclasses import dataclass`。
- 模块级配置或常量名称：`SESSION_STATE_KEY`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/turn.py#L1-L182)。
<!-- /kb:file -->
