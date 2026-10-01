---
title: "common-auto-memory 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# common-auto-memory 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_memory/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cc2f3d51d53743503989f832d468ca90d5f8f74589af35ac6163236c28b5bba6 -->
**`jiuwenswarm/agents/harness/common/auto_memory/__init__.py`**

- 源码对模块职责的说明：Auto Memory module for jiuwenswarm.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from jiuwenswarm.agents.harness.common.auto_memory.extraction_runner import`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/__init__.py#L1-L23)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_memory/extract_memories.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b937b0c99e29bc99e8266456675f7a9c427fa4bef19ad3e8fed0f2576fb486ea -->
**`jiuwenswarm/agents/harness/common/auto_memory/extract_memories.py`**

- 源码对模块职责的说明：Extract memories from conversation after it ends.。
- 调用入口 `scan_memory_files(memory_dir)`；声明返回 `list[dict[str, Any]]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import re`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/extract_memories.py#L1-L137)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_memory/prompts.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3089c6fb40e007c2f672a00696d847472d663de711c6d4ed512e960b561af7d6 -->
**`jiuwenswarm/agents/harness/common/auto_memory/prompts.py`**

- 源码对模块职责的说明：Prompt templates for Auto Memory extraction.。
- 调用入口 `build_extract_memories_prompt(new_messages_count, existing_memories, language)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/prompts.py#L1-L197)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9b7c62003e4703557b4321b9f5adf009910aa34bd46afc38d45f1ee7fd0f484a -->
**`jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py`**

- 源码对模块职责的说明：AutoMemoryToolRestrictionRail - restrict tool calls for extract_memories subagent.。
- `AutoMemoryToolRestrictionRail` 继承 `AgentRail`；方法入口：`__init__`, `before_tool_call`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from pathlib import Path`；`from typing import Any, Dict`。
- 模块级配置或常量名称：`UNRESTRICTED_READ_TOOLS`, `READ_ONLY_BASH_COMMANDS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_memory/tool_restriction_rail.py#L1-L353)。
<!-- /kb:file -->
