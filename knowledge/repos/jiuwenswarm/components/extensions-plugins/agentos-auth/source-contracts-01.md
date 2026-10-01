---
title: "agentos-auth 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# agentos-auth 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/extensions/agentos/auth/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c23e18190ec3f20787ce4b9bf7b984a8b71e975df6089d01721f85d16139bc2e -->
**`jiuwenswarm/extensions/agentos/auth/__init__.py`**

- 源码对模块职责的说明：AgentOS authentication modules.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.extensions.agentos.auth.credential_authenticator import Au`；`from jiuwenswarm.extensions.agentos.auth.ssh_authenticator import SshPublic`；`from jiuwenswarm.extensions.agentos.auth.ssh_key_issuer import AgentOSSshKe`；`from jiuwenswarm.extensions.agentos.auth.ssh_key_registry import KeyRegistr`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/auth/__init__.py#L1-L29)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/agentos/auth/common.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6771d5e03da6ff259dda0ede8c4dc183df6b337f1d725ae2dcb509adaac7029c -->
**`jiuwenswarm/extensions/agentos/auth/common.py`**

- 源码对模块职责的说明：WebSocket 握手鉴权公共工具。。
- 调用入口 `headers_to_dict(headers)`；声明返回 `dict[str, str]`。
- 调用入口 `extract_token_from_path_and_headers(path, headers)`；声明返回 `str / None`。
- 调用入口 `extract_token(ws)`；声明返回 `str / None`。
- 调用入口 `extract_headers(ws)`；声明返回 `dict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import time`；`from http import HTTPStatus`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/auth/common.py#L1-L113)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/agentos/auth/credential_authenticator.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=695fce4170f466d2708daa729379fb5cae700af5b72a34c1ace9f337cf2e3239 -->
**`jiuwenswarm/extensions/agentos/auth/credential_authenticator.py`**

- `AuthContext` 定义类型边界。
- `AuthResult` 定义类型边界。
- `CredentialAuthenticator` 继承 `ABC`；方法入口：`authenticate`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from abc import ABC, abstractmethod`；`from dataclasses import dataclass, field`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/auth/credential_authenticator.py#L1-L42)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/agentos/auth/ssh_authenticator.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fb471430625509d1ed4a320e15139801191fe8f753f3b5daafcb181771f57c82 -->
**`jiuwenswarm/extensions/agentos/auth/ssh_authenticator.py`**

- 源码对模块职责的说明：Verify SSH public-key fingerprints via KeyRegistry.。
- `SshPublicKeyAuthenticator` 继承 `CredentialAuthenticator`；方法入口：`__init__`, `registry`, `lookup_entry`, `verify`, `authenticate`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.extensions.agentos.auth.credential_authenticator import Au`；`from jiuwenswarm.extensions.agentos.auth.ssh_key_registry import KeyRegistr`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/auth/ssh_authenticator.py#L1-L71)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/agentos/auth/ssh_key_issuer.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=42f91b9fb8aff5e16fc3b5b2f3aff801af788f4a730bbfd7548c0e58fdf3bba7 -->
**`jiuwenswarm/extensions/agentos/auth/ssh_key_issuer.py`**

- 源码对模块职责的说明：Issue short-lived SSH key pairs and register public fingerprints.。
- `SshKeyIssuer` 继承 `Protocol`；方法入口：`issue_ephemeral_key`。
- `AgentOSSshKeyIssuer` 定义类型边界；方法入口：`__init__`, `registry`, `issue_ephemeral_key`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import time`；`from typing import Protocol`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/auth/ssh_key_issuer.py#L1-L93)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/agentos/auth/ssh_key_registry.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bba56048634c0fcef3ca886898654a046cc8fa04831b93adc4f5a8f8c9986836 -->
**`jiuwenswarm/extensions/agentos/auth/ssh_key_registry.py`**

- 源码对模块职责的说明：SSH public-key fingerprint registry for AgentOS identity mapping.。
- `KeyRegistryEntry` 定义类型边界。
- `KeyRegistry` 定义类型边界；方法入口：`__init__`, `register`, `lookup`, `revoke`, `cleanup_expired`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import time`；`from dataclasses import dataclass`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/auth/ssh_key_registry.py#L1-L57)。
<!-- /kb:file -->
