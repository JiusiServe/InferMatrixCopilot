---
title: "rsi-program-dataset-creator-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# rsi-program-dataset-creator-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=008eb9a18a86a356f12adab46f70b1beab3a73b52ce2366f271e333ff1878fdb -->
**`jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py`**

- 源码对模块职责的说明：Check that a task folder is complete, before handing it over.。
- 调用入口 `main()`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`import logging`；`import pathlib`。
- 模块级配置或常量名称：`TOP`, `OPTIONS`, `SPLIT`, `MANIFEST`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/rsi-program-dataset-creator/scripts/check_folder.py#L1-L218)。
<!-- /kb:file -->
