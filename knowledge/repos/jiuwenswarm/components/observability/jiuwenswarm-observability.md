---
title: "可观测性：Agent 轨迹采集、存储与保留（jiuwenswarm/observability）"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
---

# 可观测性：Agent 轨迹采集、存储与保留（jiuwenswarm/observability）

在 AgentServer 中接收 Core 产出的 OTLP span 记录，按会话写入本地 SQLite 轨迹库，并为轨迹查看器提供读取查询、按页保留清理和会话删除。它也负责维护会话的轮次（turn）身份，并把已提交的轨迹修订提示跨进程推送到 Gateway。

**从哪里读起**

- `jiuwenswarm/observability/runtime.py` — AgentServer 的轨迹运行时生命周期：start/sync/shutdown_trajectory_runtime 向 Core 注册或注销记录消费者；get_trajectory_runtime_sink 返回当前的 sink
- `jiuwenswarm/observability/session_delete.py` — 产品 Session 删除时的轨迹生命周期：begin/abort/commit_trajectory_session_delete，以及 trajectory_session_accepts_records
- `jiuwenswarm/observability/turn.py` — SessionTurnTracker/TurnIdentity：定义一个 ReAct 循环何时开启新轮次，以及 HITL 恢复、steer、supplement、cancel 各自的处理方式
- `jiuwenswarm/observability/gateway_hints.py` — TrajectoryGatewayHintBridge：把已提交的轨迹更新（CommittedTraceUpdate）作为修订提示，跨进程排队推送给 Gateway

**关键文件**

- `jiuwenswarm/observability/sink.py` — 有界的记录消费者和 SQLite 写线程：TrajectoryRecordSink 负责批量写入与重试；TrajectorySessionSinkRouter 按会话路由写入，并处理删除和过期库清扫
- `jiuwenswarm/observability/store.py` — TrajectoryStore 负责无损写入、按保留规则删除过期数据和写检查点；AsyncTrajectoryReader 提供查看器使用的读取查询
- `jiuwenswarm/observability/retention.py` — 按页的保留规划：只删除最旧的连续整页轮次，并留下检查点，保证剩余部分的渲染结果不变
- `jiuwenswarm/observability/otlp_payload.py` — 严格的 OTLP JSON 解析，要求数值有限并限制嵌套深度，决定记录是否可以交给查看器投影；读取和保留两处共用这一规则
- `jiuwenswarm/observability/models.py` — 持久化边界上的类型化记录，包括 TraceRecordData、StreamFrameData、CommittedTraceUpdate、TraceSinkStats，以及它们从 Core 记录转换而来的方法
- `jiuwenswarm/observability/config.py` — TrajectoryStoreSettings：读取轨迹存储配置，并解析每个会话的数据库路径

**改动路由**

- `jiuwenswarm/observability/`
