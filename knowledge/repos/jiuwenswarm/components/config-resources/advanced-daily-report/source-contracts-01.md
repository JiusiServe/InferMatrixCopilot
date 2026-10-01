---
title: "advanced-daily-report 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# advanced-daily-report 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/report_helper.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=68069a4d9f3af0c9b96cfe84d9239ad68d30e8e7114660a2c7a79287142faa22 -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/report_helper.py`**

- 源码对模块职责的说明：日报生成器辅助脚本。
- 调用入口 `get_workspace_dir()`；声明返回 `Path`。
- 调用入口 `read_file_safe(file_path)`；声明返回 `str`。
- 调用入口 `parse_todo_status(content)`；声明返回 `dict[str, list[dict]]`。
- 调用入口 `extract_work_summary(content)`；声明返回 `list[str]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import io`；`import json`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/report_helper.py#L1-L302)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/run_report.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=18dbd49d6ce0bd20d5c27095cbed781be7304b5b3eb49dab6db577c1b3fd88a8 -->
**`jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/run_report.py`**

- 源码对模块职责的说明：日报/周报/月报生成入口脚本（独立版）。
- 调用入口 `collect_git_stats(date)`；声明返回 `dict`。
- 调用入口 `collect_email_stats(date)`；声明返回 `dict`。
- 调用入口 `collect_email_content(limit, days)`；声明返回 `list`。
- 调用入口 `generate_daily_report(date, enable_ai)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import io`；`import os`；`import re`。
- 模块级配置或常量名称：`SKILL_DIR`, `PACKAGE_ROOT`, `REPO_ROOT`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/run_report.py#L1-L800)。
<!-- /kb:file -->
