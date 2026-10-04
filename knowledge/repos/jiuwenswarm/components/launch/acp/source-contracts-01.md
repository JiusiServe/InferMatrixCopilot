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

<!-- kb:file path=jiuwenswarm/acp/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b47046c7957d5192ac2211299ea2afdf126a8363582feaa8eaf06c65a841588c -->
**`jiuwenswarm/acp/__init__.py`**

- 源码对模块职责的说明：ACP stdio client primitives (talk to external ACP agents as a subprocess).。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.acp.stdio_client import AcpStdioClient`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/__init__.py#L1-L7)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/acp/cli.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c230bd29c9e2d7a65badef0a61bcf5a36b27011768488574b167dab12749cdac -->
**`jiuwenswarm/acp/cli.py`**

- 源码对模块职责的说明：CLI smoke test for external ACP agents (stdio), sharing config with acp_chat tool.。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import asyncio`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/cli.py#L1-L90)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/acp/subprocess_env.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6c9b8a2e73f68dda8eca4c981911b026fe38e654fbba05e5c018e6f5fbdb313a -->
**`jiuwenswarm/acp/subprocess_env.py`**

- 源码对模块职责的说明：ACP 子进程环境构造已下沉 ''jiuwenswarm.common.acp.subprocess_env''。。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.common.acp.subprocess_env import build_acp_subprocess_env`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/subprocess_env.py#L1-L12)。
<!-- /kb:file -->
