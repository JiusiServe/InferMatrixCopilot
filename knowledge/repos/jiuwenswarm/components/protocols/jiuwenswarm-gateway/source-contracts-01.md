---
title: "jiuwenswarm-gateway 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# jiuwenswarm-gateway 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/protocol/acp/acp_connect.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=943220034730eea652f5bcc525cff5611ea6903a72b939f236c2ab00eadeb057 -->
**`jiuwenswarm/gateway/channel_manager/protocol/acp/acp_connect.py`**

- `AcpChannelConfig` 定义类型边界。
- `AcpGatewayRequestContext` 定义类型边界。
- `AcpGatewayBridge` 定义类型边界；方法入口：`__init__`, `request_contexts`, `inbound_intercept`, `outbound_intercept`, `cleanup`, `handle_jsonrpc_request`。
- `AcpChannel` 继承 `BaseChannel`；方法入口：`__init__`, `channel_id`, `on_message`, `start`, `stop`, `send`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import asyncio`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/acp/acp_connect.py#L1-L1824)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/protocol/ssh/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=94c46cf6998f217040028c348632275077ab79f002125c13de6c0c7f474f6522 -->
**`jiuwenswarm/gateway/channel_manager/protocol/ssh/__init__.py`**

- 源码对模块职责的说明：SSH server channel: accept SSH clients and deliver sessions to MessageHandler.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import TYPE_CHECKING`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/__init__.py#L1-L29)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/protocol/ssh/config.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2832788e20907e519a0600d351c5d09f69609d3fc64236413333045c7a851dad -->
**`jiuwenswarm/gateway/channel_manager/protocol/ssh/config.py`**

- 源码对模块职责的说明：Configuration for the SSH server channel.。
- `ProxyConfig` 定义类型边界。
- 调用入口 `proxy_config_from_dict(raw)`；声明返回 `ProxyConfig`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from pathlib import Path`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/config.py#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/protocol/ssh/key_registry.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bf75ca004383669805ed9e6fdd0e93c00a9eed301731011d6a4d8d8efc936e88 -->
**`jiuwenswarm/gateway/channel_manager/protocol/ssh/key_registry.py`**

- 源码对模块职责的说明：Compatibility re-exports for AgentOS SSH key registry types.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.extensions.agentos.auth.ssh_key_issuer import SshKeyIssuer`；`from jiuwenswarm.extensions.agentos.auth.ssh_key_registry import KeyRegistr`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/key_registry.py#L1-L13)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=58d0161ae26647fb819aea1c593ea6a9e359843fb43ee3ced219c30886e72d14 -->
**`jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py`**

- 源码对模块职责的说明：SSH proxy server: accept clients and hand off to MessageHandler.。
- `SSHAgentHooks` 定义类型边界。
- `ProxySSHServer` 继承 `asyncssh.SSHServer if ASYNCSSH_AVAILABLE else obje`；方法入口：`__init__`, `connection_made`, `begin_auth`, `password_auth_supported`, `public_key_auth_supported`, `validate_public_key`。
- `SSHProxy` 定义类型边界；方法入口：`__init__`, `start`, `stop`, `wait_closed`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import uuid`；`from dataclasses import dataclass`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py#L1-L290)。
<!-- /kb:file -->
