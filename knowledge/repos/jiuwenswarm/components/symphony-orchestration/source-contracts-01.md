---
title: "symphony-orchestration 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# symphony-orchestration 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/symphony/experience.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1495cfd43cb4875f5de5d241daa3b2466dbc09ed135cded38f03174145568137 -->
**`jiuwenswarm/symphony/experience.py`**

- 源码对模块职责的说明：JiuwenSwarm adapters for Symphony execution evidence and packages.。
- `PublishedCapabilitySnapshotProvider` 定义类型边界；方法入口：`__init__`, `snapshot_capabilities`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from copy import deepcopy`；`from dataclasses import replace`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/experience.py#L1-L329)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/symphony/llm.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f3ca29c773d847dcdf74dbbc6b5c2973e2ddf2d87bad402ab6a231ee86774e9b -->
**`jiuwenswarm/symphony/llm.py`**

- 源码对模块职责的说明：LLM helpers backed by JiuwenSwarm's configured model stack.。
- `LLMConfig` 定义类型边界；方法入口：`from_default_model`, `from_model_entry`, `from_model`, `backend`, `base_url`, `model_client_kwargs`。
- 调用入口 `register_request_model(model)`；声明返回 `str`。
- 调用入口 `resolve_request_llm_config(reference)`；声明返回 `LLMConfig`。
- 调用入口 `bind_request_llm_config(reference)`；声明返回 `Token`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import hashlib`；`import json`；`from collections import defaultdict`。
- 模块级配置或常量名称：`LLM_IDENTITY_SCHEMA_VERSION`, `SYMPHONY_LLM_CONFIG_REF_KEY`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/llm.py#L1-L731)。
<!-- /kb:file -->
