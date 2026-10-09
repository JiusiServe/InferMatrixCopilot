---
title: "agent-server-runtime 审查规则"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [jiuwenswarm, components]
sources: ["PR #7625"]
confidence: high
---

# agent-server-runtime 审查规则

## JW-WS-AUDIT-1a — AgentServer 流审计限定请求本地计数，不能改变响应块

- 触发：修改 xiaoyi_0.2.4.beta3 agent_ws_server._handle_stream_impl 的 stream_audit。
- 强制：计数状态限定本次请求，样本数量与长度有界；只观察 chat.reasoning/chat.delta，保持原始流处理与交付顺序；有计数帧才用既有 logger 记录轮级汇总。
- 禁止：从计数逻辑修改、过滤 chunk；为逐块诊断新增长期日志输出；将这一实现写成与小艺字典相同的 64 条淘汰机制或声称已有独立 try/except。
- 验收：交替帧和空流分别检查计数、样本上限、汇总条件与响应块不变；任何新增异常隔离以实际代码与测试为据。^[PR #7625]
