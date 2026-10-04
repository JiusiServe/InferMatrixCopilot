---
title: "skill-creator-normal-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# skill-creator-normal-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/aggregate_benchmark.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d6b5985f73370ed79a349969ec43de65f2b340c3949080f7ec8b60ce45a21de5 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/aggregate_benchmark.py`**

- 源码对模块职责的说明：Aggregate individual run results into benchmark summary statistics.。
- 调用入口 `calculate_stats(values)`；声明返回 `dict[str, float]`。
- 调用入口 `load_run_results(benchmark_dir)`；声明返回 `dict[str, list]`。
- 调用入口 `aggregate_results(results)`；声明返回 `dict[str, Any]`。
- 调用入口 `generate_benchmark(benchmark_dir, skill_name, skill_path)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import json`；`import logging`；`import math`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/aggregate_benchmark.py#L1-L498)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/generate_report.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=40713835f8519aee2a1021f19a37e2a98e352bd9efde5ed7219379beee6d3f1e -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/generate_report.py`**

- 源码对模块职责的说明：Generate an HTML report from run_loop.py output.。
- 调用入口 `generate_html(data, auto_refresh, skill_name)`；声明返回 `str`。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import html`；`import json`；`import logging`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/generate_report.py#L1-L443)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/improve_description.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7f1c7f51d92831f82a1616734ba309ecba5c4e46610bb5b2dbc563abdccb6a61 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/improve_description.py`**

- 源码对模块职责的说明：Improve a skill description based on eval results.。
- `SkillContext` 定义类型边界。
- `EvalContext` 定义类型边界。
- `ImproveOptions` 定义类型边界。
- 调用入口 `improve_description(skill, eval_ctx, options)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import json`；`import logging`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/improve_description.py#L1-L396)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/package_skill.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=67235429a5aafa73a3db2b59c9799c7f1e85fdddfec56a7ff724ea564d0409d2 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/package_skill.py`**

- 源码对模块职责的说明：Skill Packager - Creates a distributable .skill file of a skill folder.。
- 调用入口 `should_exclude(rel_path)`；声明返回 `bool`。
- 调用入口 `package_skill(skill_path, output_dir)`；声明返回 `Path / None`。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import fnmatch`；`import logging`；`import sys`；`import zipfile`。
- 模块级配置或常量名称：`EXCLUDE_DIRS`, `EXCLUDE_GLOBS`, `EXCLUDE_FILES`, `ROOT_EXCLUDE_DIRS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/package_skill.py#L1-L160)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/quick_validate.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bcdb321a145b5f22f447e782e909d6964f12f5e5fdef333d399c884c4e37b043 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/quick_validate.py`**

- 源码对模块职责的说明：Quick validation script for skills - minimal version.。
- 调用入口 `validate_skill(skill_path)`；声明返回 `tuple[bool, str]`。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import logging`；`import re`；`import sys`；`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/quick_validate.py#L1-L181)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/run_eval.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=44ffa0421658ae88316cc96ac568f039409b299e66570758845e8cb5b4119ec2 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/run_eval.py`**

- 源码对模块职责的说明：Run trigger evaluation for a skill description.。
- `SkillInfo` 定义类型边界。
- `EvalContext` 定义类型边界。
- `EvalConfig` 定义类型边界。
- 调用入口 `find_project_root()`；声明返回 `Path`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import json`；`import logging`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/run_eval.py#L1-L411)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/run_loop.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9aad06da60696be3ebb5ed805a6118f456dc2cc0f2bde3fc59581f8ac662efa9 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/run_loop.py`**

- 源码对模块职责的说明：Run the eval + improve loop until all pass or max iterations reached.。
- `LoopConfig` 定义类型边界。
- `LoopPaths` 定义类型边界。
- 调用入口 `split_eval_set(eval_set, holdout, seed)`；声明返回 `tuple[list[dict], list[dict]]`。
- 调用入口 `run_loop(eval_set, description_override, config, paths)`；声明返回 `dict[str, Any]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`import argparse`；`import json`；`import logging`；`import os`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/run_loop.py#L1-L512)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/utils.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5df97bd7c3e3ce2741931f4d2903a8977c87e7d585188ffef0cbb7eff120b457 -->
**`jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/utils.py`**

- 源码对模块职责的说明：Shared utilities for skill-creator scripts.。
- 调用入口 `parse_skill_md(skill_path)`；声明返回 `tuple[str, str, str]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from pathlib import Path`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/skill-creator-normal/scripts/utils.py#L1-L61)。
<!-- /kb:file -->
