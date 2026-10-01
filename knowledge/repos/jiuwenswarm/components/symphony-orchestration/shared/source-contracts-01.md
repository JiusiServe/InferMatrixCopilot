---
title: "shared 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# shared 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/symphony/shared/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b4e2746d581a9c32d999154cd3dbf7a7581b64374ddd6245aa62834fffe75c3f -->
**`jiuwenswarm/symphony/shared/__init__.py`**

- 集成依赖（导入声明，不等于全部运行时依赖）：`from .storage import S3Location, create_s3_client, download_s3_object_to_pa`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/shared/__init__.py#L1-L29)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/symphony/shared/llm_payload.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f9f25d36e504627797c92ca09a62dba2bc5d5ba91e9d06466f3ded0c1fe47acb -->
**`jiuwenswarm/symphony/shared/llm_payload.py`**

- 源码对模块职责的说明：Shared helpers for compact LLM request payloads.。
- 调用入口 `compact_json(payload)`；声明返回 `str`。
- 调用入口 `prune_empty(value)`；声明返回 `Any`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/shared/llm_payload.py#L1-L32)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/symphony/shared/profiling.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=06a1c80ce9fa1fbe9e1e11a9325e34f53d08067434c040835f710a027fb05bcd -->
**`jiuwenswarm/symphony/shared/profiling.py`**

- `StageTimer` 定义类型边界；方法入口：`__init__`, `phase`, `finish`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from contextlib import contextmanager`；`from time import perf_counter`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/shared/profiling.py#L1-L40)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/symphony/shared/rich_compat.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bf861ce045af1755376af3de74af7622946524371c1e4affd186ce63d1feaecf -->
**`jiuwenswarm/symphony/shared/rich_compat.py`**

- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/shared/rich_compat.py#L1-L79)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/symphony/shared/storage.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=38c8ac0d7326096fdaea8e0850ec84eeb840b6d7f62b596f07f7c665a0c8ced4 -->
**`jiuwenswarm/symphony/shared/storage.py`**

- `S3Location` 定义类型边界；方法入口：`uri`。
- 调用入口 `is_s3_uri(value)`；声明返回 `bool`。
- 调用入口 `parse_s3_uri(uri, require_key)`；声明返回 `S3Location`。
- 调用入口 `join_s3_uri(base_uri, *parts)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from contextlib import suppress`；`from dataclasses import dataclass`；`from hashlib import sha1`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/shared/storage.py#L1-L298)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/symphony/shared/tags.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9faf37f7ad0ddfe9504d42a6ad20f9a1f766ac1b352379e9b5287d15bd04dd4d -->
**`jiuwenswarm/symphony/shared/tags.py`**

- 调用入口 `normalize_tags(*values)`；声明返回 `tuple[str, ...]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Iterable, Mapping, Set`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/shared/tags.py#L1-L66)。
<!-- /kb:file -->
