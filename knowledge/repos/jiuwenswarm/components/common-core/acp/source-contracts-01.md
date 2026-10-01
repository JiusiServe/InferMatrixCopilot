---
title: "acp 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# acp 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/common/acp/stdio_client.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d5a4fa1894daaaddd03463410b93d991608f3702d0f7a641ed56f27b11ff9110 -->
**`jiuwenswarm/common/acp/stdio_client.py`**

- 源码对模块职责的说明：Minimal ACP JSON-RPC client over subprocess stdin/stdout.。
- `AcpStdioClient` 定义类型边界；方法入口：`__init__`, `session_id`, `is_connected`, `connect`, `chat`, `aclose`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/acp/stdio_client.py#L1-L670)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/common/acp/subprocess_env.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fd464e9bd3ae39e26ad34b28ee6109a6b4473e315d62f75ecb16fb72aecb2f70 -->
**`jiuwenswarm/common/acp/subprocess_env.py`**

- 源码对模块职责的说明：Build subprocess environment for external ACP agents (Codex CLI, etc.).。
- 调用入口 `build_acp_subprocess_env(profile_env)`；声明返回 `dict[str, str]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`from typing import Any`；`from jiuwenswarm.common.config import resolve_env_vars`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/acp/subprocess_env.py#L1-L56)。
<!-- /kb:file -->
