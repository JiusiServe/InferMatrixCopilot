---
title: "packages-jiuwenswarm-tui 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# packages-jiuwenswarm-tui 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=packages/jiuwenswarm-tui/jiuwenswarm_tui/app.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=29e18da0560533d2a0daefae13182c08395712c350f17aab6912bf6e8c308417 -->
**`packages/jiuwenswarm-tui/jiuwenswarm_tui/app.py`**

- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import platform`；`import shutil`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/packages/jiuwenswarm-tui/jiuwenswarm_tui/app.py#L1-L102)。
<!-- /kb:file -->

<!-- kb:file path=packages/jiuwenswarm-tui/setup.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=33a84df638e5dacc55cd228ced5126b0447d00390af017e9f1841f0aeae75cde -->
**`packages/jiuwenswarm-tui/setup.py`**

- `BinaryDistribution` 继承 `Distribution`；方法入口：`has_ext_modules`。
- `PlatformBdistWheel` 继承 `_bdist_wheel`；方法入口：`finalize_options`, `get_tag`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`from setuptools import setup`；`from setuptools.dist import Distribution`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/packages/jiuwenswarm-tui/setup.py#L1-L31)。
<!-- /kb:file -->
