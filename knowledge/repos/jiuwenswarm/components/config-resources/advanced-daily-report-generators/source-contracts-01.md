---
title: "advanced-daily-report-generators 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# advanced-daily-report-generators 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e441f651a335db7e987310bb2484317f367f9892168efaf45f035a8fa5780aa8 -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/__init__.py`**

- 源码对模块职责的说明：报告生成模块。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .report_generator import ReportGenerator, ReportConfig`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/__init__.py#L1-L13)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cc8680e49d155bfaceb32f6635a97fe4aa696761c6b1b74c58c06603d43d6a75 -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py`**

- 源码对模块职责的说明：报告生成器。
- `ReportConfig` 定义类型边界。
- `ReportGenerator` 定义类型边界；方法入口：`__init__`, `generate_daily`, `generate_weekly`, `generate_monthly`。
- 调用入口 `main()`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import asyncio`；`import json`；`import logging`；`from dataclasses import dataclass, field`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py#L1-L506)。
<!-- /kb:file -->
