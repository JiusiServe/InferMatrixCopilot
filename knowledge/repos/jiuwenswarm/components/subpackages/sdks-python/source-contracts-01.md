---
title: "sdks-python 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# sdks-python 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=sdks/python/src/jiuwenswarm_sdk/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=50819b357a290be8f3bf1e85485b8e89a7b88366643d6e543c84b2a11a80d814 -->
**`sdks/python/src/jiuwenswarm_sdk/__init__.py`**

- 源码对模块职责的说明：No Runtime import or background process occurs on SDK import.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .client import Client, InteractionRequired, ProtocolError, TransportEr`；`from .types import AgentDefinition, Mode, QueryOperation, RunInput, Workspa`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/__init__.py#L1-L18)。
<!-- /kb:file -->

<!-- kb:file path=sdks/python/src/jiuwenswarm_sdk/protocol.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c048968ef5f92b89dd78077fd6f17bc51dac30323499906f3b073d63c846b280 -->
**`sdks/python/src/jiuwenswarm_sdk/protocol.py`**

- 源码对模块职责的说明：Incremental envelope checks only; Agent/policy semantics stay in Runtime.。
- `ProtocolError` 继承 `RuntimeError`。
- 调用入口 `encode(record)`；声明返回 `bytes`。
- `Records` 定义类型边界；方法入口：`__init__`, `accept`, `finish`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import math`；`from typing import Any`。
- 模块级配置或常量名称：`SCHEMA_VERSION`, `MAX_INPUT_BYTES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/protocol.py#L1-L147)。
<!-- /kb:file -->

<!-- kb:file path=sdks/python/src/jiuwenswarm_sdk/types.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5408a2156330efa48539219fdbcff0cb2cbb694c0173746276a8f75266e87861 -->
**`sdks/python/src/jiuwenswarm_sdk/types.py`**

- 源码对模块职责的说明：Optional typing helpers. Runtime remains the definition/policy validator.。
- `Workspace` 继承 `TypedDict`。
- `AgentDefinition` 继承 `TypedDict`。
- `RunInput` 继承 `TypedDict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from typing import Literal, NotRequired, TypedDict`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/sdks/python/src/jiuwenswarm_sdk/types.py#L1-L45)。
<!-- /kb:file -->
