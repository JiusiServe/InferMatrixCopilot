---
title: "gateway-message-handler 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# gateway-message-handler 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/gateway/message_handler/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=25d0d8e5a71ef4c53bb0cb6da444fa14ca26e8c510023489fabcfc991c62343d -->
**`jiuwenswarm/gateway/message_handler/__init__.py`**

- 源码对模块职责的说明：Message handler module.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.gateway.message_handler.message_handler import MessageHand`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/__init__.py#L1-L9)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/message_handler/command_parser/slash_command.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4e3f7b7471b64968c40fc0baf7194e0e74ce207eab3a1ad517a6f723a74326ad -->
**`jiuwenswarm/gateway/message_handler/command_parser/slash_command.py`**

- 源码对模块职责的说明：Gateway 受控通道 slash 指令：单一解析与注册表（无 IO）.。
- `GatewaySlashCommand` 继承 `str, Enum`。
- `ModeSubcommand` 继承 `str, Enum`。
- `SwitchSubcommand` 继承 `str, Enum`。
- `ParsedControlAction` 继承 `str, Enum`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from enum import Enum`；`import re`。
- 模块级配置或常量名称：`CONTROL_MESSAGE_TEXTS`, `FIRST_BATCH_REGISTRY`, `BUILTIN_COMMANDS_META`, `VALID_MODE_LINES`, `VALID_MODE_SUBCOMMANDS`, `VALID_SWITCH_LINES`, `VALID_SWITCH_SUBCOMMANDS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/command_parser/slash_command.py#L1-L726)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/message_handler/evolution_approval.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=de4b3e9a976000f59dab9b799e1cabc4499303084dcd7c23a7876964c6e4f69e -->
**`jiuwenswarm/gateway/message_handler/evolution_approval.py`**

- 源码对模块职责的说明：Evolution approval state coordination for the gateway message handler.。
- `EvolutionApprovalChunkDecision` 定义类型边界。
- `DeferredEvolutionApproval` 定义类型边界。
- `EvolutionApprovalFinishResult` 定义类型边界。
- `EvolutionApprovalCoordinator` 定义类型边界；方法入口：`__init__`, `is_current_pending`, `pending_request_id`, `deferred_request_ids`, `mark_pending`, `mark_session_in_progress`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import secrets`；`import time`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/evolution_approval.py#L1-L361)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/message_handler/join_exit_handlers.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=73903fd059c27d2c78c7ea7b7bae966f468f246f66b481d3d7523bb26a17987c -->
**`jiuwenswarm/gateway/message_handler/join_exit_handlers.py`**

- 源码对模块职责的说明：团队成员 /join /exit 处理逻辑。。
- `JoinExitHandlers` 定义类型边界；方法入口：`__init__`, `is_allowed_when_joined`, `sender_has_joined`, `join_slash_handler`, `notify_godview_member_join`, `notify_godview_member_exit`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import logging`；`import secrets`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/join_exit_handlers.py#L1-L661)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/message_handler/message_handler.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=de59eafe4f23f887c25082ef41ecd381c807bd67085e31f8eac569c49bc385ed -->
**`jiuwenswarm/gateway/message_handler/message_handler.py`**

- 源码对模块职责的说明：MessageHandler - 消息处理抽象与双队列实现（入队经 AgentServerClient 发往 AgentServer）.。
- 调用入口 `apply_a2ui_text_fallback_to_gateway_payload(payload, channel_id)`；声明返回 `dict[str, Any]`。
- 调用入口 `normalize_legacy_health_check_relay_payload(payload)`；声明返回 `dict[str, Any]`。
- `ChannelMode` 继承 `str, Enum`；方法入口：`is_team_mode`。
- 调用入口 `channel_mode_from_str(mode_str)`；声明返回 `ChannelMode`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import asyncio`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L1-L5516)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/message_handler/prompts/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7214a312f9e08e350eeaf3d579473079b9f80d51a403b5dca29565c961d01e43 -->
**`jiuwenswarm/gateway/message_handler/prompts/__init__.py`**

- 调用入口 `response_language_line()`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.common.config import get_config`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/prompts/__init__.py#L1-L11)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/message_handler/prompts/review_prompt.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=69de9e0b360b5cc1dd5d0201b47530fbee41d24b5f93a989ff2031f503c7ea90 -->
**`jiuwenswarm/gateway/message_handler/prompts/review_prompt.py`**

- 源码对模块职责的说明：PR 审查 prompt（单一数据源）.。
- 调用入口 `build_review_prompt(pr_arg)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.gateway.message_handler.prompts import response_language_l`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/prompts/review_prompt.py#L1-L39)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f64dd9370769d37d3663e728a29c5cf421c1e2e320f6d72dc67a69dfac05a79a -->
**`jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py`**

- `GitPreExecError` 继承 `Exception`。
- 调用入口 `build_security_review_prompt(extra_arg, cwd)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import subprocess`；`from jiuwenswarm.gateway.message_handler.prompts import response_language_l`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/prompts/security_review_prompt.py#L1-L263)。
<!-- /kb:file -->
