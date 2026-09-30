---
title: "Runtime Session 协调器（jiuwenswarm/runtime/session/）"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
---

# Runtime Session 协调器（jiuwenswarm/runtime/session/）

负责产品层 Session 的生命周期和执行协调，包括注册与关闭会话、调度单次（unary）和流式执行、投递 control 请求，以及取消执行及其子执行。另外维护一个有容量上限的执行登记表，记录排队中、运行中和最近结束的执行，并为每个 Session 提供一个工作调度器。

**从哪里开始读**

- `jiuwenswarm/runtime/session/coordinator.py` — RuntimeSessionCoordinator 是对外入口，提供 register_session、run_unary/submit_unary、run_stream、deliver_control、cancel_execution、c

**关键文件**

- `jiuwenswarm/runtime/session/coordinator.py` — 管理会话记录、执行句柄的创建和取消（含子执行和心跳根）、control 请求的认领与转发，以及会话状态刷新
- `jiuwenswarm/runtime/session/execution_registry.py` — SessionExecutionRegistry 负责执行状态流转（running/awaiting_control/waiting/terminal），终态记录按容量和 TTL 淘汰
- `jiuwenswarm/runtime/session/work_scheduler.py` — SessionWorkScheduler 为每个 Session 分配一条 lane（按 generation 区分），负责排队执行、取消排队项、关闭时清空队列
- `jiuwenswarm/runtime/session/model.py` — 共享模型：会话/执行状态枚举、SessionWorkKind、执行句柄与快照、取消和关闭的结果，以及超时和已结束异常

**相关文档**

- `TESTING.md` — 为本模块新增或修改测试时参考。其中部分路径可能已过期，先对照 tests/ 下已有的用例

**改动路由**

- `jiuwenswarm/runtime/session/`
