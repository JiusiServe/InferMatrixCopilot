---
title: "agentos-agentos-router 审查规则"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [jiuwenswarm, components]
sources: ["PR #7837", "PR #7838"]
confidence: high
---

# agentos-agentos-router 审查规则

## JW-AGENTOS-REG-1a — 注册缺少 placement 时留空，真实 IP 就绪后再补写

- 触发：修改 AgentOS registry_client.register_agent 或 router_client placement 补写。
- 强制：首次 address 依次取 metadata/sandbox_meta 的实际 address，否则空字符串；node 缺失也留空。沙箱 running 后从运行信息读取 node_ip/sandbox_ip（含 ip_address 别名）再 PATCH。
- 禁止：恢复 pending 等非 IP 占位值；把 instance_id 填进 address；探针未就绪时提前猜 IP。
- 验收：无 placement 时首次 POST address/node 都为空，真实 placement 到达才 PATCH；两个同源镜像 PR 只算同一条结论。^[PR #7837]^[PR #7838]
