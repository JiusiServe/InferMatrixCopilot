---
title: "Symphony 编排与能力图谱"
created: 2026-09-30
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# Symphony 编排与能力图谱

## 什么时候查这里

- 调查能力图谱（capability graph）的构建、增量状态、版本化存储与取消/恢复行为。
- 调查能力指纹（fingerprint）提取、缓存失效与 LLM 适配策略。
- 调查 Skill 检索索引（taxonomy）、经验候选（experience candidate）的推送与安装、动态 overlay 与演化开关。

## 不放什么

- Agent 运行时与演化 rail 的接线放 `components/agent-runtime/`。
- evolution 审批消息在网关/通道侧的处理放 `components/gateway-channels/`。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 图谱构建流程、checkpoint/恢复、graph_state、指纹适配、SwarmSymphonyService、经验候选安装、skill_retrieval | [Symphony 编排集成（jiuwenswarm/symphony）](jiuwenswarm-symphony.md) | 构建顺序、存储布局、取消语义、runtime 缓存键与安装守卫的源码级细节 |
| 动态 overlay 聚合、事件规范化、运行时权重、evolution 存储与迁移 | [Symphony 动态图谱演化（evolution）](jiuwenswarm-symphony-evolution.md) | 权重公式精确值、重建条件、已实现与意图的边界 |
| S3 读写、LLM 载荷精简、计时、标签归一化、rich 兼容层 | [Symphony 共享工具（symphony/shared）](jiuwenswarm-symphony-shared.md) | 底层共享工具 |

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：symphony、graph build、图谱构建、fingerprint、能力指纹、evolution、经验演进、experience candidate、recipe、skill taxonomy、skill retrieval、orchestration。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| symphony、graph build、图谱构建、fingerprint、能力指纹、evolution、经验演进、experience candidate、… | 入口 | `components/agent-runtime/`、`components/gateway-channels/`、`jiuwenswarm/symphony/adapter.py` |

## 验证入口

`tests/unit_tests/symphony/test_graph_state.py`、`test_fingerprint_adapter.py`、`test_direct_service.py`、`test_evolution.py` 与 `test_experience_flow.py` 分别覆盖构建身份、适配、服务取消、legacy overlay 和 Flow 候选安装。

## 专题入口

- [Symphony 服务、规划与经验候选安装](jiuwenswarm-symphony-service.md) — 说明进程内服务的构建互斥、规划 runtime、经验候选审批安装和 Skill taxonomy 适配；图谱构建与版本产物由 Symphony 主页面说明。

- [Symphony 图谱与经验安装的设计取舍](design-tradeoffs.md) — 设计选择、收益与代价，以及 API、配置和关联功能入口。
- [Symphony 检索与图谱编排 功能知识](feature-symphony.md)
- [evolution](evolution/_index.md)
- [symphony-orchestration 源码接口与集成边界 01](source-contracts-01.md)
- [shared](shared/_index.md)
- [skill-retrieval](skill-retrieval/_index.md)
- [Symphony 检索与图谱编排：实现深读](feature-depth-symphony.md)
- [Symphony orchestration service (jiuwenswarm/symphony/service.py) 基础知识页](knowledge.md)
