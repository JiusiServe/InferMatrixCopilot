---
title: "common-prompt 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-prompt 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/prompt/browser_task_prompt.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4f2bf3cd8496b10f112f35f613035785d3c0851868e72e627368f760497ff6e0 -->
**`jiuwenswarm/agents/harness/common/prompt/browser_task_prompt.py`**

- 源码对模块职责的说明：Browser guidance appended to agent-core's subagent tool section.。
- 调用入口 `build_browser_task_prompt(language)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/prompt/browser_task_prompt.py#L1-L70)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/prompt/priority_registry.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fa415a06509fc106ad6e186a418a1f00a4d8f86de5d93ab9766b887520ede0ca -->
**`jiuwenswarm/agents/harness/common/prompt/priority_registry.py`**

- 源码对模块职责的说明：Priority policy for JiuwenSwarm system prompts.。
- `SystemPromptPriority` 继承 `IntEnum`。
- `PromptPriorityRegistry` 定义类型边界；方法入口：`__init__`, `priority_for`, `names_for_priority`, `register_section`, `unregister_section`, `priorities`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from enum import IntEnum, unique`；`from threading import RLock`；`from types import MappingProxyType`。
- 模块级配置或常量名称：`SYSTEM_PROMPT_PRIORITY_REGISTRY`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/prompt/priority_registry.py#L1-L243)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/prompt/prompt_builder.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2d50d39043b7f8790a287b5b03652c81232804431cad185b353b55b4a516dcdd -->
**`jiuwenswarm/agents/harness/common/prompt/prompt_builder.py`**

- 源码对模块职责的说明：Stable JiuwenSwarm prompt sections for the general agent.。
- `PromptPriority` 继承 `IntEnum`。
- `LocalSectionName` 定义类型边界。
- 调用入口 `build_agent_identity_prompt(language)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from enum import IntEnum`；`from typing import Optional`；`from openjiuwen.harness.prompts import PromptSection, SystemPromptBuilder, `。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/prompt/prompt_builder.py#L1-L275)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/prompt/shell_environment.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5150faca76dae868eddc10d8781a16acf89c193ef4ba90b0522a4444a614ec6e -->
**`jiuwenswarm/agents/harness/common/prompt/shell_environment.py`**

- 源码对模块职责的说明：Build dynamic shell environment prompt fragments.。
- 调用入口 `build_shell_environment_prompt(language, os_type)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import shutil`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/prompt/shell_environment.py#L1-L159)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/prompt/user_prompt_builder.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f66aa8115ee7670088b0dcd7ec4058c752fc655ac9582097b28b13a5e91c687a -->
**`jiuwenswarm/agents/harness/common/prompt/user_prompt_builder.py`**

- 源码对模块职责的说明：User prompt helpers for multimodal image attachments.。
- 调用入口 `is_image_content_block(part)`；声明返回 `bool`。
- 调用入口 `extract_multimodal_image_files(params)`；声明返回 `list[dict[str, Any]]`。
- 调用入口 `set_current_multimodal_image_files(image_files)`；声明返回 `Any`。
- 调用入口 `reset_current_multimodal_image_files(token)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import base64`；`import copy`；`import json`。
- 模块级配置或常量名称：`IMAGE_CONTENT_OMITTED`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/prompt/user_prompt_builder.py#L1-L364)。
<!-- /kb:file -->
