---
title: "agent-creator-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# agent-creator-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/init_template.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9a24849fc3c53716913a3730c7ad1ad3e1fc5a33f10912efe3a60fa53333f3c6 -->
**`jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/init_template.py`**

- 源码对模块职责的说明：Agent Template Initializer — Creates a new agent template package。
- 调用入口 `write_stdout(text)`；声明返回 `None`。
- 调用入口 `get_jiuwenswarm_data_dir()`；声明返回 `Path`。
- 调用入口 `get_agent_workspace_dir()`；声明返回 `Path`。
- 调用入口 `get_agent_templates_local_dir()`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import os`；`import re`；`import sys`；`from pathlib import Path`。
- 模块级配置或常量名称：`MANIFEST_TEMPLATE`, `README_TEMPLATE`, `PERSONA_TEMPLATE`, `NAME_RE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/init_template.py#L1-L236)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/register_template.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8cecdcff409ff0fcc68aff5ddba0e6adccb108a6ba347e43749302d32120a824 -->
**`jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/register_template.py`**

- 源码对模块职责的说明：Register a local agent_template package in marketplace.json.。
- 调用入口 `write_stdout(text)`；声明返回 `None`。
- 调用入口 `get_jiuwenswarm_data_dir()`；声明返回 `Path`。
- 调用入口 `get_agent_workspace_dir()`；声明返回 `Path`。
- 调用入口 `get_agent_templates_local_dir()`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import os`。
- 模块级配置或常量名称：`NAME_RE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/register_template.py#L1-L273)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_hot_load_worker.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e2a876847c73271e6f9f7cca942a896c56a3499ccde1ac99bdd3cf8781e13613 -->
**`jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_hot_load_worker.py`**

- 源码对模块职责的说明：L2 hot-load worker — runs in a dedicated subprocess.。
- 调用入口 `write_stdout(text)`；声明返回 `None`。
- 调用入口 `main()`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import inspect`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_hot_load_worker.py#L1-L380)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f4e0e405c633f6804eda916cae42915c4caedca7130d380d6927cdb13eb00c86 -->
**`jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py`**

- 源码对模块职责的说明：Agent Template Validator — 分层校验 agent 模板包。。
- 调用入口 `write_stdout(text)`；声明返回 `None`。
- `Layer` 定义类型边界；方法入口：`__init__`, `error`, `warn`, `note`, `skip`, `tag`。
- 调用入口 `get_jiuwenswarm_data_dir()`；声明返回 `Path`。
- 调用入口 `get_agent_workspace_dir()`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import ast`；`import json`。
- 模块级配置或常量名称：`HOT_LOAD_WORKER`, `HOT_LOAD_TIMEOUT_SEC`, `LAYER_QUALITY`, `LAYER_STATIC`, `LAYER_HOT_LOAD`, `NAME_RE`, `TODO_MARKER`, `TODO_SCAN_SUFFIXES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/agent-creator/scripts/validate_template.py#L1-L991)。
<!-- /kb:file -->
