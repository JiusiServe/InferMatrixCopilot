---
title: "mcp_exec_command 跨平台命令执行工具"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/command_tools.py:L1129-L1145, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/command_tools.py:L881-L885, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/command_tools.py:L990-L1020, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/command_tools.py:L83-L103, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/command_tools.py:L1221-L1223]
feature: "command-execution-tool"
entry_points: ["jiuwenswarm/agents/harness/common/tools/command_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/command_tools.py", "jiuwenswarm/agents/harness/common/tools/command_execution_context.py", "jiuwenswarm/agents/harness/common/tools/command_runtime.py"]
---

# mcp_exec_command 跨平台命令执行工具

<!-- kb:knowledge owner=feature-command-execution-tool facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**设置项与默认值**

环境变量 `MCP_EXEC_COMMAND_MAX_TIMEOUT_SECONDS` 设定超时上限，未设置时默认 600（解析失败时取 3600），用户传入的 `timeout_seconds` 被夹到 `[1, max]`。非 Windows 上 `JW_START_NEW_SESSION`（默认 "true"，取值 `0/false/no/off` 之一则关闭）控制是否对子进程设置 `start_new_session=True`。沙箱路径下，启动器配置 `extra_params` 中 `fallback_on_failure` 为 True 或 `excluded_commands` 非空会被视为 host fallback 风险，命令被直接拒绝（fail-closed 错误），而非真正回退到宿主机执行。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/command_tools.py:L1129–L1145](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_tools.py#L1129-L1145), [jiuwenswarm/agents/harness/common/tools/command_tools.py:L881–L885](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_tools.py#L881-L885), [jiuwenswarm/agents/harness/common/tools/command_tools.py:L990–L1020](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_tools.py#L990-L1020)

<!-- kb:knowledge owner=feature-command-execution-tool facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**测试支撑点**

模块暴露 `reset_tui_spawn_history()`，docstring 标注用于测试，可清空 `_TUI_SPAWN_HISTORY` 来重置 TUI spawn 预算状态。TUI 预算的过期桶由 `_purge_stale_tui_spawn_buckets` 机会式清理（每窗口至多一次，删除全部条目均已过期的桶），防止会话字典无限增长。所示文件片段中没有出现其他测试入口。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/command_tools.py:L83–L103](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_tools.py#L83-L103), [jiuwenswarm/agents/harness/common/tools/command_tools.py:L1221–L1223](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/command_tools.py#L1221-L1223)

