---
title: "harmonyos-dev-suite-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# harmonyos-dev-suite-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/harmonyos-dev-suite/scripts/install_atomic_skill.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5276ea0786c90716bf3d0724b9d12f0636b6be389e8052e67d6ba27574cd1365 -->
**`jiuwenswarm/resources/agent/workspace/skills/harmonyos-dev-suite/scripts/install_atomic_skill.py`**

- 源码对模块职责的说明：Install an optional HarmonyOS atomic Skill from a local source checkout.。
- 调用入口 `install_skill(source, target, name, force)`；声明返回 `dict`。
- 调用入口 `main(argv)`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import json`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/harmonyos-dev-suite/scripts/install_atomic_skill.py#L1-L159)。
<!-- /kb:file -->
