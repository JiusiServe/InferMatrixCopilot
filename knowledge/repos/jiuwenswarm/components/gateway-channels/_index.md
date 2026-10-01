---
title: "Gateway 与频道"
created: 2026-09-30
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# Gateway 与频道

- [CLI 频道（jiuwenswarm/channels/cli）](jiuwenswarm-channels-cli.md) — `jiuwenswarm chat` 的连接握手（connection.ack）、chat.send 请求与 agent_ref、SIGINT 中断、team/plan 终止判定和 human/JSON/JSONL 三种渲染。
- [进程式 CLI 频道（process_cli）](jiuwenswarm-channels-process-cli.md) — REPL 每命令一个 worker 与斜杠命令、app.run 会话操作提交时机、机器模式的 SessionLease/Agent 绑定与停机顺序。

两页都覆盖 `jiuwenswarm/channels/` 下的频道实现；Gateway 自身的网络协议与路由不在这里。

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：cli、chat、命令行、CLI 频道、gateway client、websocket、tui、renderer、jsonl、spinner、SIGINT、受信目录。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| cli、chat、命令行、CLI 频道、gateway client、websocket、tui、renderer、jsonl、spinner、SIGINT、… | 入口 | `jiuwenswarm/channels/cli/`、`jiuwenswarm/channels/process_cli/` |

- [Process CLI 频道（jiuwenswarm/channels/process_cli）审查规则](rules.md)

## 专题入口

- [进程式 CLI 机器执行、会话租约与停机](jiuwenswarm-process-cli-machine.md) — 一次性执行的跨进程所有权、完成证据与清理边界。
