---
title: "runtime-debug-trace 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# runtime-debug-trace 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/server/runtime/debug_trace/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aaa83e42d61b41f217ba813771e8555f23d4f779a8333d6edee2efa0ae985af4 -->
**`jiuwenswarm/server/runtime/debug_trace/__init__.py`**

- 源码对模块职责的说明：Agent/Code debug trace — request-level human-readable dump.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.server.runtime.debug_trace.config import DebugTraceSetting`；`from jiuwenswarm.server.runtime.debug_trace.context import get_debug_trace_`；`from jiuwenswarm.server.runtime.debug_trace.directives import strip_debug_d`；`from jiuwenswarm.server.runtime.debug_trace.paths import debug_trace_dir, d`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/__init__.py#L1-L42)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/debug_trace/context.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7c7f5ef159e9bd10c202768c29fca24453b24b80e421b57df33b284ea02c0763 -->
**`jiuwenswarm/server/runtime/debug_trace/context.py`**

- 源码对模块职责的说明：Process-wide ContextVar bridging a run's :class:'DebugTraceLogger' to the subagent dispatch sites (''TaskTool'' in the SDK, ''AgentTool'' in jiuwenswarm).。
- 调用入口 `get_debug_trace_logger()`；声明返回 `Optional['DebugTraceLogger']`。
- 调用入口 `set_debug_trace_logger(logger)`；声明返回 `Token`。
- 调用入口 `reset_debug_trace_logger(token)`；声明返回 `None`。
- 调用入口 `register_debug_trace_logger(session_id, logger)`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`from contextvars import ContextVar, Token`；`from typing import TYPE_CHECKING, Optional`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/context.py#L1-L85)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/debug_trace/directives.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=28a928bf2891474a99a85c1ae5c6f04c071b7ba93c9ae1bcabb959ddc66ae1b6 -->
**`jiuwenswarm/server/runtime/debug_trace/directives.py`**

- 源码对模块职责的说明：Slash directive parsing — shared between Agent/Code and Team modes.。
- 调用入口 `strip_slash_directive(query, prefix)`；声明返回 `tuple[str, bool]`。
- 调用入口 `strip_debug_directive(query)`；声明返回 `tuple[str, bool]`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import re`。
- 模块级配置或常量名称：`DEBUG_PREFIX`；实际值与使用条件见源码。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/directives.py#L1-L88)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/debug_trace/paths.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a049e84666acf7872cabb8b04b18945da107ae3524bc0ce4a6e8c83640f27229 -->
**`jiuwenswarm/server/runtime/debug_trace/paths.py`**

- 源码对模块职责的说明：Debug trace directory / file resolution.。
- 调用入口 `debug_trace_dir(mode)`；声明返回 `Path`。
- 调用入口 `debug_trace_file(mode, session_id)`；声明返回 `Path`。
- 调用入口 `resolve_debug_trace_mode(runtime_mode, original_mode)`；声明返回 `str`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import re`；`from pathlib import Path`；`from jiuwenswarm.common.utils import get_user_workspace_dir`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/paths.py#L1-L58)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/debug_trace/subagent_capture.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=04ee899d497ee0dfcdd15d88b4d12152675b3f7f1a4c74b34b369c7ced696bb5 -->
**`jiuwenswarm/server/runtime/debug_trace/subagent_capture.py`**

- 源码对模块职责的说明：Capture a subagent's stream into the active run's debug dump.。
- 异步入口 `invoke_subagent_with_trace(subagent, inputs, session, session_id, source_label)`；声明返回 `dict`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/subagent_capture.py#L1-L135)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/server/runtime/debug_trace/task_tool_patch.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=03f5ef454e2b220bda5c0a07a8fad37a973a1d730d0987ccb38633a2edab99a6 -->
**`jiuwenswarm/server/runtime/debug_trace/task_tool_patch.py`**

- 源码对模块职责的说明：Attach subagent stream capture without replacing SDK TaskTool semantics.。
- 调用入口 `apply_task_tool_debug_patch()`；声明返回 `None`。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from __future__ import annotations`；`import logging`；`from typing import Any`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/task_tool_patch.py#L1-L92)。
<!-- /kb:file -->
