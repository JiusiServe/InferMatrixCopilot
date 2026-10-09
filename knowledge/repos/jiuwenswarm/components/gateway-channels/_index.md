---
title: "Gateway 与频道"
created: 2026-09-30
updated: 2026-10-09
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
| cli、chat、命令行、CLI 频道、gateway client、websocket、tui、renderer、jsonl、spinner、SIGINT、… | 入口 | `jiuwenswarm/channels/`、`jiuwenswarm/channels/cli/`、`jiuwenswarm/channels/process_cli/` |


- [Process CLI 频道（jiuwenswarm/channels/process_cli）审查规则](rules.md)

## 专题入口

- [进程式 CLI 机器执行、会话租约与停机](jiuwenswarm-process-cli-machine.md) — 一次性执行的跨进程所有权、完成证据与清理边界。

- [CLI 与会话结果交付的设计取舍](design-tradeoffs.md) — 设计选择、收益与代价，以及 API、配置和关联功能入口。
- [机器执行与本地 CLI 功能知识](feature-process-cli.md)
- [交互式命令行 功能知识](feature-cli.md)
- [SSH 频道与远程终端 功能知识](feature-ssh.md)
- [飞书 频道 功能知识](feature-im-feishu.md)
- [微信 频道 功能知识](feature-im-wechat.md)
- [企业微信 频道 功能知识](feature-im-wecom.md)
- [钉钉 频道 功能知识](feature-im-dingtalk.md)
- [小艺 频道 功能知识](feature-im-xiaoyi.md)
- [Slack 频道 功能知识](feature-im-slack.md)
- [Telegram 频道 功能知识](feature-im-telegram.md)
- [Discord 频道 功能知识](feature-im-discord.md)
- [WhatsApp 频道 功能知识](feature-im-whatsapp.md)
- [channels-cli](channels-cli/_index.md)
- [channels-process-cli](channels-process-cli/_index.md)
- [gateway](gateway/_index.md)
- [gateway-channel-manager](gateway-channel-manager/_index.md)
- [gateway-cron](gateway-cron/_index.md)
- [gateway-health-check](gateway-health-check/_index.md)
- [gateway-heartbeat](gateway-heartbeat/_index.md)
- [gateway-hooks](gateway-hooks/_index.md)
- [gateway-im-pipeline](gateway-im-pipeline/_index.md)
- [gateway-message-handler](gateway-message-handler/_index.md)
- [gateway-routing](gateway-routing/_index.md)
- [机器执行与本地 CLI：实现深读](feature-depth-process-cli.md)
- [交互式命令行：实现深读](feature-depth-cli.md)
- [SSH 频道与远程终端：实现深读](feature-depth-ssh.md)
- [飞书 频道：实现深读](feature-depth-im-feishu.md)
- [微信 频道：实现深读](feature-depth-im-wechat.md)
- [企业微信 频道：实现深读](feature-depth-im-wecom.md)
- [钉钉 频道：实现深读](feature-depth-im-dingtalk.md)
- [小艺 频道：实现深读](feature-depth-im-xiaoyi.md)
- [Slack 频道：实现深读](feature-depth-im-slack.md)
- [Telegram 频道：实现深读](feature-depth-im-telegram.md)
- [Discord 频道：实现深读](feature-depth-im-discord.md)
- [WhatsApp 频道：实现深读](feature-depth-im-whatsapp.md)
- [Gateway Web 频道处理器（channel_manager/web/app_web_handlers.py）](knowledge-gateway-channels.md)
- [进程式 CLI 频道（process_cli）：REPL、worker 与会话操作](knowledge.md)
- [/security-review 安全审查斜杠命令与 git 预执行](feature-channel-security-review-slash-command.md)
- [Gateway Config-Save Hot Reload（_on_config_saved：agent.reload_config 重试、重启兜底与副作用）](feature-gateway-config-hot-reload.md)
- [Gateway HealthCheck 周期探活服务 (jiuwenswarm/gateway/health_check)](feature-gateway-health-check.md)
- [GatewayServer 多路由 WebSocket 宿主与会话/请求路由表](feature-gateway-server-multi-route-ws.md)
- [IM Attachment Persist Hook (E2A + HTTP Bridge) — ChannelManager wiring](feature-im-attachment-persist-hook-969909e1.md)
- [IM Channel Hot Reconfiguration (_apply_channel_config lifecycle across 11 channels)](feature-im-channel-hot-reconfig.md)
- [界面语言配置 RPC（preferred_language）— Gateway Web Handler](feature-locale-conf-rpc.md)
- [3rdagent.list / 3rdagent.switch 第三方智能体切换](feature-thirdagent-list-switch.md)
- [@path 文件引用内联与 @agent 提及解析（MessageHandler）](feature-at-file-reference-inlining-b1a822e1.md)
- [scripts](scripts/_index.md)

- [@path 文件引用内联与 @agent 提及解析：实现深读](feature-depth-at-file-reference-inlining-b1a822e1.md)

- [/security-review 安全审查斜杠命令与 git 预执行：实现深读](feature-depth-channel-security-review-slash-command.md)

- [Gateway Config-Save Hot Reload (agent.reload_config retry, restart fallback, browser/proactive side effects)：实现深读](feature-depth-gateway-config-hot-reload.md)

- [Gateway HealthCheck 周期探活服务：实现深读](feature-depth-gateway-health-check.md)

- [GatewayServer 多路由 WebSocket 宿主与会话/请求路由表：实现深读](feature-depth-gateway-server-multi-route-ws.md)

- [IM Attachment Persist Hook (E2A + HTTP Bridge)：实现深读](feature-depth-im-attachment-persist-hook-969909e1.md)

- [IM Channel Hot Reconfiguration (_apply_channel_config lifecycle across 11 channels)：实现深读](feature-depth-im-channel-hot-reconfig.md)

- [界面语言配置 RPC（preferred_language）：实现深读](feature-depth-locale-conf-rpc.md)

- [3rdagent.list / 3rdagent.switch 第三方智能体切换：实现深读](feature-depth-thirdagent-list-switch.md)
