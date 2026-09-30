---
title: "Symphony 编排集成（jiuwenswarm/symphony）"
created: 2026-09-30
updated: 2026-09-30
type: architecture
tags: [jiuwenswarm]
sources: []
---

# Symphony 编排集成（jiuwenswarm/symphony）

把公开的 openjiuwen.symphony 编排 API 接入 JiuwenSwarm。模块负责进程内的 Symphony 服务、能力图谱的构建与版本化存储、能力指纹、执行经验的演进和候选安装，以及基于 Skill 分类体系（taxonomy）的索引构建。

**入口**

- `jiuwenswarm/symphony/service.py` — SwarmSymphonyService 和 get_swarm_symphony_service：进程内唯一的服务对象。负责图谱状态、刷新、取消构建，也负责 plan、经验候选的列出、请求和安装
- `jiuwenswarm/symphony/build.py` — SymphonyGraphBuilder、build_graph 和 graph_status：图谱构建流程，包括扫描、指纹、checkpoint 和产物发布
- `jiuwenswarm/symphony/config.py` — load_symphony_config 和 SymphonyConfig：Symphony 运行时配置的入口，含路径、指纹、构建、演进和编排模式
- `jiuwenswarm/symphony/skill_retrieval/runtime.py` — SkillTaxonomyRuntime：Skill 分类索引的 build/status/cancel 接口，是公开 taxonomy SDK 的一层薄适配

**关键文件**

- `jiuwenswarm/symphony/adapter.py` — 把 Swarm 配置转换成公开 Symphony API 需要的能力提供者、指纹 LLM 适配器和 orchestration/graph 配置
- `jiuwenswarm/symphony/graph_state.py` — GraphState 和 GraphStateBuilder：持久化能力哈希，用来做增量构建
- `jiuwenswarm/symphony/graph_storage.py` — 图谱产物的版本化目录、manifest 指针、发布逻辑，以及查找未完成的构建
- `jiuwenswarm/symphony/experience.py` — 执行轨迹的截断兼容处理、图谱演进 rail、submit_evolution，以及已发布能力的快照
- `jiuwenswarm/symphony/llm.py` — LLMConfig、按请求绑定模型、token 用量统计，以及 JiuwenSwarmChatClient 的 JSON 补全
- `jiuwenswarm/symphony/config.py` — 各子配置的解析和取值约束，以及 symphony/evolution 开关的判定

**改动路由**

- `jiuwenswarm/symphony/adapter.py`
- `jiuwenswarm/symphony/build.py`
- `jiuwenswarm/symphony/config.py`
- `jiuwenswarm/symphony/experience.py`
- `jiuwenswarm/symphony/graph_state.py`
- `jiuwenswarm/symphony/graph_storage.py`
- `jiuwenswarm/symphony/llm.py`
- `jiuwenswarm/symphony/service.py`
- `jiuwenswarm/symphony/skill_retrieval/`
