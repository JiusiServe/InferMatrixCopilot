---
title: "channels-cli 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# channels-cli 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/cli/_terminal.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a15255cb7c3cc1de79367e905a9243c04cc4abf8c4d70897785c0c409a75ede0 -->
**`jiuwenswarm/channels/cli/_terminal.py`**

- 源码对模块职责的说明：Low-level terminal output primitives for CLI chat.。
- 调用入口 `write_stdout(text)`；声明返回 `None`。
- 调用入口 `write_stderr(text)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import os`；`import sys`。
- 模块级配置或常量名称：`STDOUT_FD`, `STDERR_FD`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/cli/_terminal.py#L1-L48)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/cli/main.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=63f303decb2d62d3fb02456dd49157f994fcc4da6ff6612ad186de4ffdf001e3 -->
**`jiuwenswarm/channels/cli/main.py`**

- 源码对模块职责的说明：Root ''jiuwenswarm'' CLI entry point.。
- 调用入口 `main()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`import os`；`import sys`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/cli/main.py#L1-L55)。
<!-- /kb:file -->
