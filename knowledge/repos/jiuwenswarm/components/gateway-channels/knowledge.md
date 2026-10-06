---
title: "进程式 CLI 频道（process_cli）：REPL、worker 与会话操作"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:.doc_project_maintainer/project/flows/runtime-session-reference-chain.md:L66-L70, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:.doc_project_maintainer/modules/runtime-session/README.md:L42-L45, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/repl.py:L371-L379, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/repl.py:L407-L414, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/repl.py:L484-L487, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/commands.py:L75-L116, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/repl.py:L228-L275, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/repl.py:L297-L330, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/repl.py:L738-L763, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/process_cli/live_layout.py:L23-L61]
---

# 进程式 CLI 频道（process_cli）：REPL、worker 与会话操作

<!-- kb:knowledge owner=gateway-channels-2 facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**验证入口**

维护者文档列出确定性 Runtime Session 测试与真实模型门禁：tests/system_tests/test_process_cli_session_runtime_live.py 覆盖 Work/Code 两轮恢复，以及 chat 与 Goal ask_user 首轮流结束后由回答恢复确切交互并得到终止响应；该文档自述 2026-09-10 全量受影响范围验证通过（四个配置模型门禁与 AgentServer/Gateway WebSocket 路由等）。代码内注释另指出 _run_worker 对无 stdout 读取器的“轻量进程替身”做了兼容，说明存在依赖该替身的频道生命周期测试。以上均为文档与代码可见证据，本轮输入未运行任何测试。

Sources / 来源：[.doc_project_maintainer/project/flows/runtime-session-reference-chain.md:L66–L70](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/.doc_project_maintainer/project/flows/runtime-session-reference-chain.md#L66-L70), [.doc_project_maintainer/modules/runtime-session/README.md:L42–L45](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/.doc_project_maintainer/modules/runtime-session/README.md#L42-L45), [jiuwenswarm/channels/process_cli/repl.py:L371–L379](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/repl.py#L371-L379)

<!-- kb:knowledge owner=gateway-channels-2 facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**入口与结果契约**

公开入口是 repl.run_repl(args) -> int，内部循环读取提示词并分发。_run_worker 返回 (return_code, next_session)：worker 退出码非 0/130 时向 stderr 输出含日志尾部的诊断；130（用户中断）由 repl.py 中 cancel_requested 或 CancelledError 分支赋值，app.run 遇到 CancelledError 则渲染中断事件后重新抛出而非返回 130。本地命令注册表由 commands.py 的 SLASH_COMMANDS 提供，parse_slash_command 把名称规范化为不带参数解释的 ParsedSlashCommand。

Sources / 来源：[jiuwenswarm/channels/process_cli/repl.py:L407–L414](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/repl.py#L407-L414), [jiuwenswarm/channels/process_cli/repl.py:L484–L487](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/repl.py#L484-L487), [jiuwenswarm/channels/process_cli/commands.py:L75–L116](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/commands.py#L75-L116)

<!-- kb:knowledge owner=gateway-channels-2 facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**会话操作与运行中输入**

REPL 支持会话 create/switch（/resume、别名 /continue）/fork（/branch、别名 /fork）/delete：/delete 需交互确认，成功删除当前会话后清空 state.session_id；/sessions 打开分页浏览（n/p 翻页、s 搜索、序号选择）。chat 运行期间父进程把非斜杠输入作为补充转发到 worker stdin，并用 LiveTurnLayout 在单一 prompt 应用中展示请求、补充（含回执标记）、通知与模型输出；/cancel 通过 SIGINT（Windows 为 CTRL_BREAK_EVENT）→ terminate → kill 的梯度中断 worker。

Sources / 来源：[jiuwenswarm/channels/process_cli/repl.py:L228–L275](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/repl.py#L228-L275), [jiuwenswarm/channels/process_cli/repl.py:L297–L330](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/repl.py#L297-L330), [jiuwenswarm/channels/process_cli/repl.py:L738–L763](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/repl.py#L738-L763), [jiuwenswarm/channels/process_cli/live_layout.py:L23–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/process_cli/live_layout.py#L23-L61)

