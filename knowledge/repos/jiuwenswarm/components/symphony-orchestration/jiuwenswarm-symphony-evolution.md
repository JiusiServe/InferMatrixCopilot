---
title: "Symphony 动态图谱演化（evolution）"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
---

# Symphony 动态图谱演化（evolution）

本模块把 Symphony 运行时事件（如计划结果、选中的技能、边的成败和失败归因）追加写入图谱目录下的 evolution 存储。它再把这些事件聚合成动态图谱 overlay，按边、节点、路径统计结果并计算运行时权重，供加载和查询状态使用。

**从这里读起**

- `jiuwenswarm/symphony/evolution/service.py` — 对外的服务函数：record_plan_outcome 记录计划结果，load_dynamic_overlay / rebuild_dynamic_overlay 加载或重建 overlay，evolution_status 返回演化状态，

**关键文件**

- `jiuwenswarm/symphony/evolution/aggregate.py` — build_overlay_from_events 把事件聚合成 overlay，逐条累计边、节点、路径的结果并计算 _runtime_weight
- `jiuwenswarm/symphony/evolution/store.py` — 只追加的文件存储：events、overlay、skill packs 各自的路径和读写函数，以及 evolution_store_transaction 事务
- `jiuwenswarm/symphony/evolution/models.py` — 共享的 key 和归一化函数：edge_key、skill_id，以及边、结果（outcome）、失败归因的归一化
- `jiuwenswarm/symphony/evolution/service.py` — 判断 overlay 是否需要重建（按图谱版本和事件时间），给失败的边加标注，并提供默认失败归因

**路由**

- `jiuwenswarm/symphony/evolution/`
