---
title: "CLI 频道（jiuwenswarm/channels/cli）"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
---

# CLI 频道（jiuwenswarm/channels/cli）

提供根命令 `jiuwenswarm` 的 CLI 入口和命令行聊天频道：解析参数，通过兼容 `/tui` 的 WebSocket 连接 Gateway，再把流式事件渲染成人类可读、JSON 或 JSONL 输出。交互模式下还负责权限确认和用户输入、Ctrl+C（SIGINT）中断，以及受信目录的持久化和清理。

**从这里读起**

- `jiuwenswarm/channels/cli/main.py` — 根命令 `jiuwenswarm` 的 CLI 入口 `main()`
- `jiuwenswarm/channels/cli/chat.py` — chat 命令的编排入口：`build_parser` 定义参数，`run_chat` 连接 Gateway 并运行 interactive、json 或 jsonl 循环

**关键文件**

- `jiuwenswarm/channels/cli/chat.py` — 参数校验、请求构造、spinner、SIGINT 处理（含 Windows 分支）、受信目录状态读写和权限卡片应答
- `jiuwenswarm/channels/cli/gateway_client.py` — `GatewayClient`：兼容 `/tui` 的 WebSocket 客户端，负责 connect、send_request、recv 和 close；`set_mock_ws` 供测试注入
- `jiuwenswarm/channels/cli/render.py` — `HumanRenderer`、`JsonRenderer`、`JsonlRenderer`，分别处理三种输出模式下的 delta、reasoning、tool_call、final 和 error 事件
- `jiuwenswarm/channels/cli/events.py` — 事件判定：内容是否结束、流是否终止、是否需要用户输入，以及事件归类
- `jiuwenswarm/channels/cli/_terminal.py` — 用 `os.write` 实现的终端输出原语；按 docstring 所说，这是终端 UI，不是日志，所以没有走 `logging`（G.LOG.02）

**相关文档**

- `docs/zh/Quickstart.md` — 想了解用户通常怎样启动和使用命令行时读
- `README_CN.md` — 需要项目总体介绍，或核对 CLI 在整体架构里的位置时读
- `docs/zh/FAQ.md` — PR 改动连接提示、报错文案或常见使用问题时读
- `TESTING.md` — PR 新增或修改 CLI 测试时参考；其中有过期路径，要先对照 tests/ 下已有的用例

**改动路由**

- `jiuwenswarm/channels/cli/`
