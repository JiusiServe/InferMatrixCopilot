---
title: "advanced-daily-report-analyzers 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# advanced-daily-report-analyzers 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/analyzers/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=55c2a4a11edf0578fae37aa8ba53d4c15202c9a554ed0232a25264a2f95f9fa7 -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/analyzers/__init__.py`**

- 源码对模块职责的说明：进阶版日报生成器 - 分析模块。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .work_analyzer import WorkAnalyzer, EfficiencyMetrics, TrendComparison`；`from .ai_analyzer import AIAnalyzer, AIAnalysisResult, WorkPatternResult`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/analyzers/__init__.py#L1-L35)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/analyzers/ai_analyzer.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c9c6a48e68873cb8e38b6700e08a2846d9e8231a4a146a683fd15506b42f4aa1 -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/analyzers/ai_analyzer.py`**

- 源码对模块职责的说明：AI 智能分析器。
- `AIAnalysisResult` 定义类型边界；方法入口：`to_dict`。
- `WorkPatternResult` 定义类型边界；方法入口：`to_dict`。
- `AIAnalyzer` 定义类型边界；方法入口：`__init__`, `generate_summary_sync`, `generate_summary`, `suggest_tomorrow`, `analyze_work_pattern`, `analyze_full`。
- 调用入口 `analyze_sync(data, config_path)`；声明返回 `AIAnalysisResult`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import asyncio`；`import json`；`import logging`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/analyzers/ai_analyzer.py#L1-L474)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/analyzers/work_analyzer.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ed98a01b452463ba4e1d7120a49884fb80f838c4aeac0cf3044e9ea9c0143f91 -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/analyzers/work_analyzer.py`**

- 源码对模块职责的说明：工作分析引擎。
- `EfficiencyMetrics` 定义类型边界；方法入口：`to_dict`。
- `TrendComparison` 定义类型边界；方法入口：`to_dict`。
- `AnalysisResult` 定义类型边界；方法入口：`to_dict`。
- `WorkAnalyzer` 定义类型边界；方法入口：`__init__`, `calculate_metrics`, `generate_comparison`, `analyze`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import json`；`import re`；`from collections import Counter`；`from dataclasses import dataclass, field`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/analyzers/work_analyzer.py#L1-L453)。
<!-- /kb:file -->
