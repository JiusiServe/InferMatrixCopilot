---
title: "server-runtime 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# server-runtime 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/text_formatter.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=007574ee10fa6a993c1dd2b542fabbb05d110a0aa85110d98ebff03bbbe572a9 -->
**`jiuwenswarm/server/runtime/a2ui/text_formatter.py`**

- 源码对模块职责的说明：Format A2UI responses into plain text for fallback paths.。
- 调用入口 `format_for_text_channel(content, parse_response, validate_response)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from collections.abc import Callable`；`from typing import Any`；`from a2ui.schema.constants import A2UI_OPEN_TAG`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/text_formatter.py#L1-L113)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/types.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1b6eed6e21d49c880fdb9cdb6ae98080729adc1b341ab1c5988d5c0ac942ca94 -->
**`jiuwenswarm/server/runtime/a2ui/types.py`**

- 源码对模块职责的说明：Shared A2UI runtime data structures.。
- `A2UIResponsePart` 定义类型边界。
- `A2UIExample` 定义类型边界。
- `A2UIValidationResult` 定义类型边界。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from dataclasses import dataclass`；`from pathlib import Path`；`from typing import Any, Literal`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/types.py#L1-L35)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/a2ui/validator.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fbbff1eebbfc0fd6f050ceb6893ffdca2011df8a370b7c14afe17f709ae6079d -->
**`jiuwenswarm/server/runtime/a2ui/validator.py`**

- 源码对模块职责的说明：A2UI schema and runtime semantic validation.。
- 调用入口 `validate_a2ui_messages(catalog, messages)`；声明返回 `None`。
- 调用入口 `validate_a2ui_response(content, parse_response, validate_messages)`；声明返回 `A2UIValidationResult`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import json`；`from collections.abc import Callable`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/a2ui/validator.py#L1-L305)。
<!-- /kb:file -->
