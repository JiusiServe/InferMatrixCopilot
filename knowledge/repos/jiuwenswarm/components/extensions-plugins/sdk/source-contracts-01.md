---
title: "sdk 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# sdk 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/extensions/sdk/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a0b06d1c77fdf77cefc206b3e23bc478365bffe5b37dd626fe1167f3d7567ba1 -->
**`jiuwenswarm/extensions/sdk/__init__.py`**

- 源码对模块职责的说明：Extension SDK exports; transport-specific contracts are lazy imports.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from importlib import import_module`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/sdk/__init__.py#L1-L61)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/sdk/agent_server_client.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=936ae0e7f15c648ed2bd12587f6847bdfc826d43db2c3420cc32e076d5d85d08 -->
**`jiuwenswarm/extensions/sdk/agent_server_client.py`**

- `AgentServerClientExtension` 继承 `BaseExtension`；方法入口：`get_client`, `shutdown`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from abc import abstractmethod`；`from jiuwenswarm.common.client.agent_client import AgentServerClient`；`from jiuwenswarm.extensions.sdk.base import BaseExtension`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/sdk/agent_server_client.py#L1-L17)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/sdk/crypto_utility.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=45c139f0092ec757ec3ce764fd594fe786f7b57cc775357af90c0ebb7055a6f8 -->
**`jiuwenswarm/extensions/sdk/crypto_utility.py`**

- `CryptoUtility` 继承 `BaseExtension`；方法入口：`get_crypto`, `shutdown`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from abc import abstractmethod`；`from jiuwenswarm.extensions.sdk.base import BaseExtension`；`from jiuwenswarm.common.security.base_crypto import CryptoProvider`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/sdk/crypto_utility.py#L1-L17)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/sdk/third_agent.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=628d1d0f5fae6cc31f4bbf518a6efb94e51f8b3d74e087de9f03e0dc3de87f7a -->
**`jiuwenswarm/extensions/sdk/third_agent.py`**

- `ThirdAgentExtension` 继承 `BaseExtension`；方法入口：`get_third_agent`, `shutdown`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from abc import abstractmethod`；`from jiuwenswarm.extensions.sdk.base import BaseExtension`；`from jiuwenswarm.common.client.third_agent import ThirdAgent`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/sdk/third_agent.py#L1-L19)。
<!-- /kb:file -->
