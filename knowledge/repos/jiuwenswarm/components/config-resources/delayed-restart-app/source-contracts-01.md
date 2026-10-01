---
title: "delayed-restart-app 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# delayed-restart-app 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/delayed-restart-app/launch_delayed_restart.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=653c7c21abdabad85bb5566d9807a3b2eb37b49150ab1d44eccffa22a7753753 -->
**`jiuwenswarm/resources/agent/workspace/skills/delayed-restart-app/launch_delayed_restart.py`**

- 源码对模块职责的说明：以 detached 方式启动 delayed_restart_app，供 bash 通过 skill 调用。。
- 调用入口 `main()`；声明返回 `int`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import argparse`；`import subprocess`；`import sys`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/delayed-restart-app/launch_delayed_restart.py#L1-L55)。
<!-- /kb:file -->
