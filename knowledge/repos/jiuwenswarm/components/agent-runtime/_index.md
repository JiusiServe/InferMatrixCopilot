---
title: "Agent 运行时与会话"
created: 2026-09-30
updated: 2026-09-30
type: index
tags: [jiuwenswarm]
sources: []
---

# Agent 运行时与会话

- [共享 Agent Runtime（jiuwenswarm/runtime）](jiuwenswarm-runtime.md)
- [Runtime Session 协调器（jiuwenswarm/runtime/session/）](jiuwenswarm-runtime-session.md)

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：runtime、AgentRuntime、session create/switch/fork、session.delete、plan mode、model catalog、permission snapshot、MCP reference、push handler、process CLI、agent definition、运行时。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| runtime、AgentRuntime、session create/switch/fork、session.delete、plan mode、model… | 入口 | `jiuwenswarm/runtime/agent_definition.py`、`jiuwenswarm/runtime/context.py`、`jiuwenswarm/runtime/events.py` |
