---
title: "common-rsi 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-rsi 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=942a31b50d42d736a8b55cfec63df744df8eae5eb9e5031dad9de1feff3ecd3f -->
**`jiuwenswarm/agents/harness/common/rsi/__init__.py`**

- 源码对模块职责的说明：RSI 服务域（agents/harness/common/rsi）—— Event Sink 主通道落地（内部接口 v3）。。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.agents.harness.common.rsi.adapter import RsiEngineAdapter,`；`from jiuwenswarm.agents.harness.common.rsi.artifact_adapter import Artifact`；`from jiuwenswarm.agents.harness.common.rsi.context import RsiServiceContext`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/__init__.py#L1-L118)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/adapter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8ecd7fbb64fec2ebb11211604bacc1b40fcf899ea1445d2275169f4cce42c3d1 -->
**`jiuwenswarm/agents/harness/common/rsi/adapter.py`**

- 源码对模块职责的说明：引擎对接适配层（内部 v3 §5 / adapter 契约 v1 §2）。。
- `EngineState` 继承 `Protocol`。
- `EngineReport` 继承 `Protocol`。
- `RsiEngineAdapter` 继承 `Protocol`；方法入口：`build_request`, `run`, `resume`, `read_state`, `read_report`, `validate_input`。
- 调用入口 `engine_event_sink_from_queue(queue)`；声明返回 `RsiEventSink`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from collections.abc import Awaitable, Callable`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/adapter.py#L1-L182)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/artifact_adapter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=538de99e6d348c6c36e2eda26ecdf5523b6ba80cdcaf17bd7c98eaae5304df58 -->
**`jiuwenswarm/agents/harness/common/rsi/artifact_adapter.py`**

- 源码对模块职责的说明：Artifact Provider adapter and public projection helpers.。
- 调用入口 `provider_status(value, default)`；声明返回 `str`。
- 调用入口 `provider_usage_to_dict(usage)`；声明返回 `dict[str, Any] / None`。
- 调用入口 `provider_artifact_to_dict(artifact)`；声明返回 `dict[str, Any]`。
- 调用入口 `provider_node_to_dict(node)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import asdict, fields, is_dataclass`；`from pathlib import Path`；`from typing import Any, Callable, Mapping`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/artifact_adapter.py#L1-L484)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/artifact_files_service.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=82ed23d82207147c077939a9cbf644a33375ee0ea55d5ea6427c5c59d845a3b3 -->
**`jiuwenswarm/agents/harness/common/rsi/artifact_files_service.py`**

- 源码对模块职责的说明：RSI 产物文件浏览服务（目录树 + 单文件读取）。。
- `RsiArtifactFilesService` 定义类型边界；方法入口：`__init__`, `list_files`, `read_file`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import base64`；`import hashlib`；`import mimetypes`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/artifact_files_service.py#L1-L286)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/artifact_service.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=56159ef85d7040e00e963eb7381d29018b5c16bcc1304987b83cf4ead9861298 -->
**`jiuwenswarm/agents/harness/common/rsi/artifact_service.py`**

- 源码对模块职责的说明：RsiArtifactService：采纳节点快照 + 下载定位（内部 v3 §4.5 / web §8.3）。。
- `RsiArtifactService` 定义类型边界；方法入口：`__init__`, `make_snapshot`, `locate`, `best_artifact`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import zipfile`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/artifact_service.py#L1-L139)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/context.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=470e4c9a944acc5a6db9637ae4deb18a78a59b0f90829d7f613043aa654cab27 -->
**`jiuwenswarm/agents/harness/common/rsi/context.py`**

- 源码对模块职责的说明：RSI 服务域组合根：装配 store/worker/projector/artifact/usage/薄服务（内部 v3 §7 复用清单）。。
- `RsiServiceContext` 定义类型边界；方法入口：`__init__`, `bind_task_service`, `bind_harness_installer`, `bind_dataset_service`, `register_adapters`, `adapter_for`。
- 调用入口 `build_rsi_service_context(tasks_root, adapters, harness_materializer, model_resolver, enable_harness_materialization, allow_missing_harness, agent_manager, harness_activation_store, harness_installer)`；声明返回 `RsiServiceContext`。
- 调用入口 `get_rsi_workspace_root()`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`from pathlib import Path`；`from typing import Any, Callable`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/context.py#L1-L340)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/errors.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0742f1b57ab33c2d3829845687f32313ba7a6892e2db3cc5a5fb9dff33df793e -->
**`jiuwenswarm/agents/harness/common/rsi/errors.py`**

- 源码对模块职责的说明：RSI 服务域错误体系（错误码对齐 web 契约 §3.5 全集）。。
- 调用入口 `failure_reason(value, fallback)`；声明返回 `str`。
- `RsiError` 继承 `Exception`；方法入口：`__init__`。
- `RsiBadRequest` 继承 `RsiError`；方法入口：`__init__`。
- `RsiScenarioNotSupported` 继承 `RsiError`；方法入口：`__init__`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/errors.py#L1-L199)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/event_consumer.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=14fc8a4249943f4d0deff5433378cde7b4ee0f19833a9e40b34ec2a2c696baa1 -->
**`jiuwenswarm/agents/harness/common/rsi/event_consumer.py`**

- 源码对模块职责的说明：RsiEventConsumer：引擎事件单协程消费者（内部 v3 §4.3）。。
- `RsiEventConsumer` 定义类型边界；方法入口：`__init__`, `bind_push`, `on_engine_event`。
- 异步入口 `consume_queue(queue, consumer)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`from collections.abc import Awaitable, Callable`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/event_consumer.py#L1-L264)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/event_journal.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4e8ae8f7258943a85b458aa080f80ba00e215c80e44787951d0a04c470063635 -->
**`jiuwenswarm/agents/harness/common/rsi/event_journal.py`**

- 源码对模块职责的说明：Append-only task journal for raw RSI engine events.。
- `RsiEventJournal` 定义类型边界；方法入口：`__init__`, `append`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import threading`；`from collections.abc import Mapping`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/event_journal.py#L1-L94)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/events.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4f99666f289622921130e6ffccc199a130e984ad9c07a91f6307f8c71ed80d5e -->
**`jiuwenswarm/agents/harness/common/rsi/events.py`**

- 源码对模块职责的说明：引擎事件模型（内部 v3 §3.3 四子类 + 公共信封）。。
- `EngineEvent` 定义类型边界；方法入口：`is_progress_metric`, `is_progress_usage`, `is_node_created`, `is_node_stage`, `to_dict`, `from_dict`。
- 调用入口 `parse_engine_event(raw, default_task_id)`；声明返回 `EngineEvent / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass, field`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/events.py#L1-L103)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/harness_adapter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ae801f91c3f8d8ce56de66b0075f33ddc26fd3cb7aca8ab20bddc799c99d6e0a -->
**`jiuwenswarm/agents/harness/common/rsi/harness_adapter.py`**

- 源码对模块职责的说明：Harness Provider adapter owned by the JiuwenSwarm RSI service.。
- `HarnessEngineRequest` 定义类型边界。
- `HarnessProviderContract` 继承 `Protocol`；方法入口：`validate_input`, `run`, `resume`, `pause`, `terminate`, `read_state`。
- `HarnessEngineAdapter` 定义类型边界；方法入口：`__init__`, `build_request`, `validate_input`, `run`, `resume`, `pause`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import asdict, dataclass, is_dataclass`；`from collections.abc import Mapping`；`from typing import Any, Protocol`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_adapter.py#L1-L217)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/harness_provider.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=39d5ffa374a73d31e5dfa4c7329c5d8e0102504dbf9e74304eba3542bc44ba07 -->
**`jiuwenswarm/agents/harness/common/rsi/harness_provider.py`**

- 源码对模块职责的说明：生产 HarnessProvider：包装 agent-core 单 Harness 迭代优化编排器。。
- 调用入口 `engine_validate_input(dataset_path)`；声明返回 `Any`。
- `HarnessProvider` 定义类型边界；方法入口：`__init__`, `validate_input`, `run`, `resume`, `pause`, `terminate`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import inspect`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/harness_provider.py#L1-L840)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/materializer.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=639e1e21c8872cc2c9214f0531d6053e4cab526df6f48c82f4b87667ab06f029 -->
**`jiuwenswarm/agents/harness/common/rsi/materializer.py`**

- 源码对模块职责的说明：Create immutable, task-private inputs for a Harness Validation run.。
- `RsiTaskMaterialization` 定义类型边界；方法入口：`to_manifest`。
- `RsiTaskMaterializer` 定义类型边界；方法入口：`__init__`, `task_dir`, `materialize_dataset`, `materialize_harness_refs`, `materialize_validation_profile`, `materialize`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import json`；`import shutil`。
- 模块级配置或常量名称：`VALIDATION_PROFILE_NAME`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/materializer.py#L1-L898)。
<!-- /kb:file -->
