---
title: "runtime 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# runtime 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/runtime/team_entity_store.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aba69ce6e1f3669b76e8230f39d78854598f119e1b3234d4245e2aaffdc79606 -->
**`jiuwenswarm/server/runtime/team_entity_store.py`**

- 源码对模块职责的说明：Persistent per-team entity metadata stored in the team workspace.。
- `TeamEntityStoreError` 继承 `ValueError`；方法入口：`__init__`。
- `TeamEntity` 定义类型边界；方法入口：`from_dict`, `to_dict`。
- `TeamEntityStore` 定义类型边界；方法入口：`__init__`, `entity_path`, `exists`, `get`, `write`, `ensure`。
- 调用入口 `get_team_entity_store()`；声明返回 `TeamEntityStore`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import shutil`；`import threading`；`import time`。
- 模块级配置或常量名称：`TEAM_ENTITY_META_DIR`, `TEAM_ENTITY_FILE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/team_entity_store.py#L1-L282)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/tenant_agent_pool.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=45089eb691bf2f1b1c167ba80d7ba7335bc57c113b4459716b3fb22377a62b4e -->
**`jiuwenswarm/server/runtime/tenant_agent_pool.py`**

- `TenantAgentPool` 定义类型边界；方法入口：`__init__`, `get_instance`, `reset_instance`, `process_message`, `process_message_stream`, `cleanup`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Any, ClassVar`；`from jiuwenswarm.common.schema.agent import AgentRequest, AgentResponse`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/tenant_agent_pool.py#L1-L89)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/tokenizer_service.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ef72b75a3fca3d7b776240447406c53a29fb3b64d5a2e18a0ba3f0947833e263 -->
**`jiuwenswarm/server/runtime/tokenizer_service.py`**

- 源码对模块职责的说明：AgentServer-side tokenizer cache warm-up service.。
- `TokenizerProfile` 定义类型边界。
- `TokenizerWarmupSettings` 定义类型边界。
- 调用入口 `resolve_tokenizer_cache_dir(config)`；声明返回 `Path`。
- 调用入口 `tokenizer_warmup_settings(config)`；声明返回 `TokenizerWarmupSettings`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import hashlib`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/tokenizer_service.py#L1-L1435)。
<!-- /kb:file -->
