---
title: "Agent 运行时与会话"
created: 2026-09-30
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# Agent 运行时与会话

## 什么时候查这里

请求规范化、会话 provision，以及 generation、lane 排队、交互输入、取消与关闭协调。

## 不放什么

持久会话元数据由服务端 session 模块拥有；cron 产生定时工作、通道处理传输，分别查对应 component。

## 目录内容

- [共享 Agent Runtime（jiuwenswarm/runtime）](jiuwenswarm-runtime.md) — 传输层无关的 Runtime：请求规范化、会话 create/switch/fork/delete、Plan 模式、模型/权限/MCP 目录
- [Runtime Session 协调器（jiuwenswarm/runtime/session/）](jiuwenswarm-runtime-session.md) — 会话执行协调：准入与 generation、lane 排队、unary/流式执行、control 投递与心跳链、取消与关闭

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：runtime、AgentRuntime、session create/switch/fork、session.delete、plan mode、model catalog、permission snapshot、MCP reference、push handler、process CLI、agent definition、运行时、session lane、execution registry、work scheduler、deliver_control、cancel_execution、close_session、QUIESCING、control input、心跳链。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| runtime、AgentRuntime、session create/switch/fork、session.delete、plan mode、model… | 入口 | `jiuwenswarm/runtime/agent_definition.py`、`jiuwenswarm/runtime/context.py`、`jiuwenswarm/runtime/events.py` |
| session 执行协调、lane 排队、deliver_control、cancel_execution、close_session | Runtime Session 协调器（见目录内容） | `jiuwenswarm/runtime/session/coordinator.py`、`jiuwenswarm/runtime/session/execution_registry.py`、`jiuwenswarm/runtime/session/work_scheduler.py` |

## 验证入口

`tests/unit_tests/runtime/test_runtime_session_coordinator.py` 覆盖进程内排序、控制输入、取消与关闭；Runtime 上层契约见共享 Runtime 页。

## 专题入口

- [Runtime 交互输入、执行取代与取消](jiuwenswarm-runtime-control.md) — 协调等待交互的执行、补充输入、工作取代和子执行取消；会话注册、lane 调度与关闭由 Runtime Session 主页面说明。

- [Runtime unary 与流式执行](jiuwenswarm-runtime-execution.md) — 提交去重、超时与取消、终态 owner 和流消费者提前退出。

- [Runtime 生命周期与协调的设计取舍](design-tradeoffs.md) — 设计选择、收益与代价，以及 API、配置和关联功能入口。
- [项目、会话与历史管理 功能知识](feature-projects-sessions.md)
- [agent-runtime 源码接口与集成边界 01](source-contracts-01.md)
