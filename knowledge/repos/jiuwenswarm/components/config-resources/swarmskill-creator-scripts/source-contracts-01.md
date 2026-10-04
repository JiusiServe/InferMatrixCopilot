---
title: "swarmskill-creator-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# swarmskill-creator-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/resources/agent/workspace/skills/swarmskill-creator/scripts/validate_swarmskill.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=95c14c436ce6641a2bddb4cc0ef150e86abf13b84f1f50329a92d6b11ca3efa4 -->
**`jiuwenswarm/resources/agent/workspace/skills/swarmskill-creator/scripts/validate_swarmskill.py`**

- 源码对模块职责的说明：validate_swarmskill.py — Compliance checker for Swarm Skills (v0.1 spec).。
- `Report` 定义类型边界；方法入口：`__init__`, `err`, `warn`, `passed`, `emit`。
- 调用入口 `split_frontmatter(text)`；声明返回 `tuple[dict[str, Any] / None, str]`。
- 调用入口 `find_h2_sections(body)`；声明返回 `dict[str, int]`。
- 调用入口 `section_body(body, header)`；声明返回 `str / None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import ast`；`import builtins`；`import sys`。
- 模块级配置或常量名称：`FRONTMATTER_RE`, `SUPPORTED_SWARMFLOW_OPERATORS`, `SUPPORTED_SWARMFLOW_TYPES`, `PROTECTED_SWARMFLOW_NAMES`, `DEFERRED_THUNK_OPERATORS`, `NON_DETERMINISTIC_IMPORTS`, `FILESYSTEM_CALLS`, `PATH_IO_METHODS`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/swarmskill-creator/scripts/validate_swarmskill.py#L1-L1795)。
<!-- /kb:file -->
