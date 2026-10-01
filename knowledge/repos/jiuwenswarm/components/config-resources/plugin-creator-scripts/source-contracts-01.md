---
title: "plugin-creator-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# plugin-creator-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dca11e222faf3d73043daf3111e1eba33f29fd2db65606b8993c971426ca00c6 -->
**`jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py`**

- 源码对模块职责的说明：Plugin Package Initializer — Creates a new plugin package。
- 调用入口 `write_stdout(text)`；声明返回 `None`。
- 调用入口 `get_jiuwenswarm_data_dir()`；声明返回 `Path`。
- 调用入口 `get_agent_workspace_dir()`；声明返回 `Path`。
- 调用入口 `get_plugin_packages_local_dir()`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import os`；`import re`；`import sys`；`from pathlib import Path`。
- 模块级配置或常量名称：`MANIFEST_TEMPLATE`, `README_TEMPLATE`, `NAME_RE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/init_plugin.py#L1-L206)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/register_plugin.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=be25c84b09d2c526eed66760d715835cf4fd22e99ac04146c8f00eda3a82b67d -->
**`jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/register_plugin.py`**

- 源码对模块职责的说明：Register a local plugin package in marketplace.json.。
- 调用入口 `write_stdout(text)`；声明返回 `None`。
- 调用入口 `get_jiuwenswarm_data_dir()`；声明返回 `Path`。
- 调用入口 `get_agent_workspace_dir()`；声明返回 `Path`。
- 调用入口 `get_plugin_packages_local_dir()`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import os`。
- 模块级配置或常量名称：`NAME_RE`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/register_plugin.py#L1-L235)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a8d4e414a52e16be6a5ad862f5521a87748a6c24bd935f8ce41eefa86ba1be6f -->
**`jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py`**

- 源码对模块职责的说明：Plugin Package Validator — 分层校验 plugin 插件包。。
- 调用入口 `write_stdout(text)`；声明返回 `None`。
- `Layer` 定义类型边界；方法入口：`__init__`, `error`, `warn`, `note`, `skip`, `tag`。
- 调用入口 `get_jiuwenswarm_data_dir()`；声明返回 `Path`。
- 调用入口 `get_agent_workspace_dir()`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import ast`；`import json`。
- 模块级配置或常量名称：`HOT_LOAD_WORKER`, `HOT_LOAD_TIMEOUT_SEC`, `LAYER_QUALITY`, `LAYER_STATIC`, `LAYER_HOT_LOAD`, `NAME_RE`, `TODO_MARKER`, `TODO_SCAN_SUFFIXES`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin.py#L1-L975)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ebeb1c00e7f5626a1b81a7c068da8fa3f50262ffb0c66cd2ae1ab8dc844feeec -->
**`jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py`**

- 源码对模块职责的说明：L2 hot-load worker for plugin packages — runs in a dedicated subprocess.。
- 调用入口 `write_stdout(text)`；声明返回 `None`。
- 调用入口 `main()`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import asyncio`；`import inspect`；`import json`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/plugin-creator/scripts/validate_plugin_hot_load_worker.py#L1-L380)。
<!-- /kb:file -->
