---
title: "SwarmFlow 工作流与 HITL：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/workflow_state.py:L832-L847]
---

# SwarmFlow 工作流与 HITL：实现深读

[功能概览](feature-swarmflow.md) · [owner 入口](_index.md)

<!-- kb:depth feature=swarmflow facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=423fa27405561bee95d6d65408294bf2f16491a5521e08c9923e113f4db05969 -->
**阶段计数采用派生重算而非增量维护**
设计推断（非作者历史意图）：

_refresh_phase_counts 每次从 phase.agents 列表重算 agent_count 与 completed_agent_count（终态集合 completed / failed / stopped）。文档字符串说明动机：拆卸路径盖终态不走计数器递增，派生方式让计数自动保持一致。代价（推断）：每次刷新都需遍历整个 agent 列表，随节点数线性增长。

来源：[jiuwenswarm/agents/harness/team/handlers/workflow_state.py:L832–L847](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/workflow_state.py#L832-L847)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/team/handlers/workflow_state.py","start":832,"end":847,"sha256":"ba57b3d7103b04f4edfc91aa27227078d9c2c09a4090286c361e46c222ad766d"}],"trace":[]} -->
<!-- /kb:depth -->
