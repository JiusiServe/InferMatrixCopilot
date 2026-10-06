---
title: "可观测性与轨迹存储"
created: 2026-09-30
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# 可观测性与轨迹存储

- [可观测性：Agent 轨迹采集、存储与保留（jiuwenswarm/observability）](jiuwenswarm-observability.md) — 准入身份校验与跨会话主体拒绝、有界双队列与快照合并/溢出计数、locked/busy 单次重试与冲突 first-wins、每会话 SQLite 路由与孤儿缓冲、Session 删除墓碑三段式、整页保留与检查点、查看器安全 OTLP 校验

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：observability、trajectory、轨迹、OTLP、trace、span、sink、SQLite、retention、保留、turn、session delete。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| observability、trajectory、轨迹、OTLP、trace、span、sink、SQLite、retention、保留、turn、sessi… | 入口 | `jiuwenswarm/observability/` |

## 专题入口

- [轨迹保留、检查点与查看器投影边界](jiuwenswarm-trajectory-retention.md) — 说明已存轨迹的整页保留、检查点、OTLP 投影与持久化类型校验；记录准入、队列、writer 和会话删除见可观测性主页面。

- [轨迹队列与存储的设计取舍](design-tradeoffs.md) — 设计选择、收益与代价，以及 API、配置和关联功能入口。
- [执行轨迹与保留 功能知识](feature-observability.md)
- [Debug Dump 与 OTel 功能知识](feature-debug-trace.md)
- [observability 源码接口与集成边界 01](source-contracts-01.md)
- [执行轨迹与保留：实现深读](feature-depth-observability.md)
- [Debug Dump 与 OTel：实现深读](feature-depth-debug-trace.md)
- [JiuwenSwarm 可观测性：轨迹存储路由、有界写入与每会话 SQLite（jiuwenswarm/observability）](knowledge.md)
