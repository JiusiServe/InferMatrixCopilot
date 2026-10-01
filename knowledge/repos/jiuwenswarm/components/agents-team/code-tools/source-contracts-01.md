---
title: "code-tools 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# code-tools 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/agents/harness/code/tools/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=83e109c21da0c82e80093191480e70dcc9bc5bc028b1498e5082187dc10f80e9 -->
**`jiuwenswarm/agents/harness/code/tools/__init__.py`**

- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.agents.harness.code.tools.code_todo_tools import CodeTodoC`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/tools/__init__.py#L1-L15)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/agents/harness/code/tools/code_todo_tools.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a75bb4bd6a8584183a06dae0e88b543df7cf229db91ff9905a1f2a2e7e5fe6b6 -->
**`jiuwenswarm/agents/harness/code/tools/code_todo_tools.py`**

- 源码对模块职责的说明：Code-mode todo tools with CC-aligned descriptions and schemas.。
- `CodeTodoCreateTool` 继承 `TodoCreateTool`；方法入口：`__init__`。
- `CodeTodoListTool` 继承 `TodoListTool`；方法入口：`__init__`。
- `CodeTodoGetTool` 继承 `TodoGetTool`；方法入口：`__init__`。
- `CodeTodoModifyTool` 继承 `TodoModifyTool`；方法入口：`__init__`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import uuid`；`from typing import Optional`；`from openjiuwen.core.foundation.tool import ToolCard`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/code/tools/code_todo_tools.py#L1-L115)。
<!-- /kb:file -->
