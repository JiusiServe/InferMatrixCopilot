---
title: "common-rsi 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-rsi 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/mock_artifact_provider.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a90199dc6f7bd26006b1e9fd3dde209c077a1a2f72ce35fb6b7cf429036d2269 -->
**`jiuwenswarm/agents/harness/common/rsi/mock_artifact_provider.py`**

- 源码对模块职责的说明：Small in-process artifact Providers for service-layer integration.。
- `MockArtifactProvider` 定义类型边界；方法入口：`__init__`, `validate_input`, `run`, `pause`, `resume`, `read_state`。
- 调用入口 `build_mock_artifact_adapters(tasks_root, model_resolver, requires_model, iteration_delay, node_delay, branching_factor)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import hashlib`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/mock_artifact_provider.py#L1-L956)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/mock_harness_provider.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ebb55b3665c33c18ae840fad8e28359224cecc5cf2dc7f326afaa9ea5db1b8e4 -->
**`jiuwenswarm/agents/harness/common/rsi/mock_harness_provider.py`**

- 源码对模块职责的说明：Deterministic Harness Provider for RSI service and Web E2E.。
- `MockHarnessProvider` 定义类型边界；方法入口：`__init__`, `validate_input`, `run`, `resume`, `pause`, `terminate`。
- 调用入口 `build_mock_harness_adapter(tasks_root)`；声明返回 `Any`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import hashlib`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/mock_harness_provider.py#L1-L694)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/model_resolver.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f48315099057207ef5b06e60c4dbb8780830592d1ef275e0265198a6b8868b49 -->
**`jiuwenswarm/agents/harness/common/rsi/model_resolver.py`**

- 源码对模块职责的说明：Resolve JiuwenSwarm model selections into openjiuwen model files.。
- `ResolvedRsiModel` 定义类型边界；方法入口：`to_manifest`。
- `RsiModelConfigResolver` 定义类型边界；方法入口：`__init__`, `entries`, `resolve`, `resolve_to_file`。
- 调用入口 `select_rsi_model_entry(entries, model_ref)`；声明返回 `tuple[dict[str, Any], int / None]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`from copy import deepcopy`；`from dataclasses import dataclass`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/model_resolver.py#L1-L306)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/models.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=29c3e04365fe9a64feca05e2d089062916d6a4f4d9f9ddd152daa50272d4fb55 -->
**`jiuwenswarm/agents/harness/common/rsi/models.py`**

- 源码对模块职责的说明：RSI 服务域公共模型（与 web 契约 v0.3 / 内部接口 v3 对齐）。。
- 调用入口 `generate_task_id()`；声明返回 `str`。
- `TaskStatus` 继承 `str, Enum`；方法入口：`terminal`。
- `Scenario` 继承 `str, Enum`。
- `ArtifactType` 继承 `str, Enum`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import uuid`；`from dataclasses import asdict, dataclass, field`；`from datetime import datetime, timezone`。
- 模块级配置或常量名称：`TASK_ID_PREFIX`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/models.py#L1-L331)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/paper_provider.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=68e47edf109a5705f4e619b5fd4966122516552ac480f1a2dbdb7cbc0dc6b95b -->
**`jiuwenswarm/agents/harness/common/rsi/paper_provider.py`**

- 源码对模块职责的说明：AgentServer Provider bridge for the OpenJiuwen paper optimizer.。
- `PaperProvider` 定义类型边界；方法入口：`__init__`, `validate_input`, `run`, `pause`, `resume`, `terminate`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import contextlib`；`import hashlib`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/paper_provider.py#L1-L1412)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/plugin_catalog.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=012fe3194b5336e4f3e648ec549f8c35db2eef3008f30461a0fbb18804c7174d -->
**`jiuwenswarm/agents/harness/common/rsi/plugin_catalog.py`**

- 源码对模块职责的说明：Publish an RSI-owned copy through the existing extension catalog APIs.。
- 调用入口 `register_harness_plugin(source, installation_id)`；声明返回 `Callable[[], None]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import json`；`import shutil`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/plugin_catalog.py#L1-L131)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/projector.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6cd32b8d8ffa0f7b1269e2b54da2daeebd6703953f47191a49a6b3f6e7b2d279 -->
**`jiuwenswarm/agents/harness/common/rsi/projector.py`**

- 源码对模块职责的说明：RsiProjector：单投影函数（事件 ↔ tree/进度/推送 同源；内部 v3 §4.4）。。
- `RsiProjector` 定义类型边界；方法入口：`__init__`, `register_root`, `on_node_created`, `on_provider_node`, `merge_provider_tree`, `sync_provider_tree`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import threading`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/projector.py#L1-L522)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/provider_factory.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1920a5870b832b9599d6d03c53ab2751b4db9f71766f461110bb120bb7faeb77 -->
**`jiuwenswarm/agents/harness/common/rsi/provider_factory.py`**

- 源码对模块职责的说明：RSI Provider assembly.。
- 调用入口 `build_mock_rsi_adapters(tasks_root, model_resolver)`；声明返回 `dict[str, Any]`。
- 调用入口 `build_rsi_adapters(tasks_root, mode, harness_provider, artifact_adapters, paper_provider, model_resolver)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from pathlib import Path`；`from typing import Any`；`from jiuwenswarm.agents.harness.common.rsi.artifact_adapter import Artifact`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/provider_factory.py#L1-L107)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/recovery.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6181d1ecdfab6e3b7da7a9f75c67854c30f42ff2f4f703bde93fefca48926787 -->
**`jiuwenswarm/agents/harness/common/rsi/recovery.py`**

- 源码对模块职责的说明：Durable workspace recovery for interrupted RSI AgentServer tasks.。
- `RsiWorkspaceRecovery` 定义类型边界；方法入口：`__init__`, `recover`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Any`；`from jiuwenswarm.agents.harness.common.rsi.errors import failure_reason`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/recovery.py#L1-L119)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/services.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4900b32e394859b1b3e4bd9d1e79d5005dd4419c277c522f60e0c8c7b7f9f9ed -->
**`jiuwenswarm/agents/harness/common/rsi/services.py`**

- 源码对模块职责的说明：派生薄封装服务（内部 v3 §4.7）：RsiDatasetService / RsiTaskService / RsiReportService / RsiTreeService。。
- `RsiTaskService` 定义类型边界；方法入口：`__init__`, `create`, `list`, `get`, `delete`, `start`。
- `RsiDatasetService` 定义类型边界；方法入口：`__init__`, `validate`。
- `RsiReportService` 定义类型边界；方法入口：`__init__`, `get`。
- `RsiTreeService` 定义类型边界；方法入口：`__init__`, `get`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import shutil`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/services.py#L1-L987)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/task_store.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b80d7e42fec86d8ba73d2495c8bdd2c316d17136a71330696cd722d5c0ba8d99 -->
**`jiuwenswarm/agents/harness/common/rsi/task_store.py`**

- 源码对模块职责的说明：RsiTaskStore：任务存储 + 状态机（内部 v3 §4.1 + 一致性规则 §8）。。
- `RsiTaskStore` 定义类型边界；方法入口：`__init__`, `task_dir`, `create`, `get`, `get_view`, `list`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import shutil`；`import threading`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/task_store.py#L1-L231)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/usage_recorder.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e44fc01b3b5e12bd18efd057c27e7363e148a6c5353bf7fde93a716769baa306 -->
**`jiuwenswarm/agents/harness/common/rsi/usage_recorder.py`**

- 源码对模块职责的说明：RsiUsageRecorder：progress.usage 事件聚合（内部 v3 §4.6）。。
- `RsiUsageRecorder` 定义类型边界；方法入口：`__init__`, `record`, `record_engine_event`, `record_cumulative`, `get`, `usage_summary`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Mapping`；`from dataclasses import asdict, is_dataclass`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/usage_recorder.py#L1-L277)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/validation_dataset.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8cb76a5fe07da5c680c327598874d5acddc51762b1d8deac791d8256632b5283 -->
**`jiuwenswarm/agents/harness/common/rsi/validation_dataset.py`**

- 源码对模块职责的说明：Normalize Evo-Bench validation suites for the single-Harness engine.。
- 调用入口 `normalize_validation_suite(source_path)`；声明返回 `dict[str, Any] / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from pathlib import Path`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/validation_dataset.py#L1-L66)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/rsi/worker.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3c852f0f899d14740f5fe73321b384fa99bbeab67b27b2ea772e96a1ce147e30 -->
**`jiuwenswarm/agents/harness/common/rsi/worker.py`**

- 源码对模块职责的说明：RsiWorker：单协程队列（并发=1）+ 事件链路装配（内部 v3 §4.2）。。
- `RsiWorker` 定义类型边界；方法入口：`__init__`, `enqueue`, `cancel`, `resume`, `register_push_callbacks`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`import time`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/rsi/worker.py#L1-L932)。
<!-- /kb:file -->
