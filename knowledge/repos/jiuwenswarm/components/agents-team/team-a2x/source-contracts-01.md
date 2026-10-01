---
title: "team-a2x 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# team-a2x 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2b926f77b63d1332e40732b02fc936c3274522fbd6cf8b18f9300df20e3ab82d -->
**`jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py`**

- 源码对模块职责的说明：Small runtime helpers for A2X registry integration.。
- `ReservedBlankAgent` 定义类型边界；方法入口：`release`, `close`。
- 调用入口 `build_teammate_agent_card(member_name)`；声明返回 `dict[str, Any]`。
- 调用入口 `resolve_a2x_config(config_base)`；声明返回 `dict[str, Any]`。
- 异步入口 `init_a2x_client(config_base)`；声明返回 `tuple[Any, dict[str, Any]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`import re`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py#L1-L548)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/team/a2x/client/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=33179728692fd66eab1656065ad372b0ff7e2d71abc006e52d61b680068cffcf -->
**`jiuwenswarm/agents/harness/team/a2x/client/__init__.py`**

- 源码对模块职责的说明：A2X Registry client SDK.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .async_client import AsyncA2XRegistryClient`；`from .client import A2XRegistryClient`；`from .errors import A2XConnectionError, A2XError, A2XHTTPError, NotFoundErr`；`from .models import AgentDetail, DatasetCreateResponse, DatasetDeleteRespon`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/__init__.py#L1-L60)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/team/a2x/client/_internal.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=724d449e8093c10e901c6a20f81368078631aaa929adb876c98fcdbb5b10eed2 -->
**`jiuwenswarm/agents/harness/team/a2x/client/_internal.py`**

- 源码对模块职责的说明：Shared helpers used by the sync and async client classes.。
- 调用入口 `dataset_path(dataset)`；声明返回 `str`。
- 调用入口 `services_path(dataset)`；声明返回 `str`。
- 调用入口 `service_path(dataset, service_id)`；声明返回 `str`。
- 调用入口 `a2a_register_path(dataset)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from pathlib import Path`；`from typing import Any, Final`；`from urllib.parse import quote`。
- 模块级配置或常量名称：`UNSET`, `DEFAULT_FORMATS`, `DEFAULT_EMBEDDING_MODEL`, `DEFAULT_OWNERSHIP_FILE`, `STATUS_FIELD`, `STATUS_ONLINE`, `STATUS_BUSY`, `STATUS_OFFLINE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/_internal.py#L1-L304)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/team/a2x/client/async_client.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=128c280dd1e1f47dbf53cadaedfee2464f9144eb7f815263bb92ed9774209216 -->
**`jiuwenswarm/agents/harness/team/a2x/client/async_client.py`**

- 源码对模块职责的说明：Asynchronous client entry point.。
- `AsyncA2XRegistryClient` 定义类型边界；方法入口：`__init__`, `base_url`, `timeout`, `api_key`, `aclose`, `create_dataset`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import warnings`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/async_client.py#L1-L393)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/team/a2x/client/client.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cfc599fb9d8b545bf56e47675e2b701b3e2db25431776a87858dc06a875ee217 -->
**`jiuwenswarm/agents/harness/team/a2x/client/client.py`**

- 源码对模块职责的说明：Synchronous client entry point.。
- `A2XRegistryClient` 定义类型边界；方法入口：`__init__`, `base_url`, `timeout`, `api_key`, `close`, `create_dataset`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from pathlib import Path`；`from typing import Any, Literal`；`import warnings`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/client.py#L1-L530)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/team/a2x/client/errors.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=17a82f8ed9f1d70d691fcc0efac34300444d5dc9bd2db0b78b81fe931ac559c1 -->
**`jiuwenswarm/agents/harness/team/a2x/client/errors.py`**

- 源码对模块职责的说明：Exception hierarchy for the A2X Registry client SDK.。
- `A2XError` 继承 `Exception`；方法入口：`__init__`。
- `A2XConnectionError` 继承 `A2XError`。
- `A2XHTTPError` 继承 `A2XError`。
- `NotFoundError` 继承 `A2XHTTPError`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/errors.py#L1-L73)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/team/a2x/client/models.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4a12789150e193eeea23911effe801399281baf46cc2b6fdf675022024b6aab8 -->
**`jiuwenswarm/agents/harness/team/a2x/client/models.py`**

- 源码对模块职责的说明：Response dataclasses for the A2X Registry client SDK.。
- `DatasetCreateResponse` 继承 `_FromDictMixin`。
- `DatasetDeleteResponse` 继承 `_FromDictMixin`。
- `RegisterResponse` 继承 `_FromDictMixin`。
- `PatchResponse` 继承 `_FromDictMixin`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from dataclasses import dataclass, field, fields`；`from typing import Any, TypeVar`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/models.py#L1-L168)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/team/a2x/client/ownership.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7a5331ce8f2c97d78b63d6d2598875dbc78b53f63aa368e80456fd46748609a3 -->
**`jiuwenswarm/agents/harness/team/a2x/client/ownership.py`**

- 源码对模块职责的说明：Persistent tracker for services registered by this client.。
- `OwnershipStore` 定义类型边界；方法入口：`__init__`, `contains`, `add`, `remove`, `remove_dataset`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import os`；`import sys`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/ownership.py#L1-L225)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/team/a2x/client/transport.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=328052e529e212ed080c522faeaf30b1b797745f6b6f597936d456b49f1dce0d -->
**`jiuwenswarm/agents/harness/team/a2x/client/transport.py`**

- 源码对模块职责的说明：Thin httpx wrappers — the SDK's only network exit.。
- `HTTPTransport` 定义类型边界；方法入口：`__init__`, `request`, `close`。
- `AsyncHTTPTransport` 定义类型边界；方法入口：`__init__`, `request`, `aclose`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any, Literal`；`import httpx`；`from .errors import A2XConnectionError, A2XHTTPError, NotFoundError, Server`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/client/transport.py#L1-L134)。
<!-- /kb:file -->
