---
title: "SwarmFlow 工作流与 HITL：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/workflow_state.py:L832-L847, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py:L75-L102, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py:L173-L187, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_workflow_monitor_handler.py:L617-L679]
feature: "swarmflow"
entry_points: ["jiuwenswarm/agents/harness/team/handlers/workflow_state.py"]
source_globs: ["jiuwenswarm/agents/harness/team/handlers/workflow_state.py", "jiuwenswarm/agents/harness/team/handlers/*"]
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

<!-- kb:depth feature=swarmflow facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0cacb067abe88008f4d14caf82cff67fb30fb4240a489f41d7378f1e929a698e -->
**单事件异常跳过与持久化失败仅告警**
触发一：单条原始事件在 `_process_event` 内抛异常；传播：`_collect_events` 的逐事件 try/except 记 error 后跳过该事件继续迭代，不终止收集循环，仅流迭代自身出错才进外层 except。触发二：`persist_workflow_runs` 抛异常；传播：`_persist` 捕获 Exception 仅记 warning（checkpoint persist failed），不向 `_process_event` 扩散。

来源：[jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py:L75–L102](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py#L75-L102), [jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py:L173–L187](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py#L173-L187)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":102,"path":"jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py","sha256":"025bdeb7fdf49fea9530abd6909b37a96489f40ff74c2a78cf473714855afaf9","start":75},{"end":187,"path":"jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py","sha256":"40f44133f21307b46b3204cdee94a7146d63ac94c773856eab94c93241c47cdc","start":173}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=swarmflow facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=39988619b3de60a9740bf8d20964c792047557c32b06eff81e7e71da03fbfe91 -->
**finalize_pending_runs 的 disposition 断言**
`tests/unit_tests/agentserver/test_workflow_monitor_handler.py::TestFinalizePendingRunsDisposition` 把 `_persist` monkeypatch 为 no-op 后直测 `finalize_pending_runs`：stop disposition 断言 running run 的 run/phase/agent 全变 `stopped`、`is_terminal is True`、`completed_at` 非空、`completed_agent_count == 1`；pause disposition 断言停在 `paused` 且 `completed_at`/`duration_ms` 为 None（不落终态字段）。此处仅记录断言行使的行为，不声称测试现已运行通过。

来源：[tests/unit_tests/agentserver/test_workflow_monitor_handler.py:L617–L679](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_workflow_monitor_handler.py#L617-L679)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":679,"path":"tests/unit_tests/agentserver/test_workflow_monitor_handler.py","sha256":"91740b2618d24fcdfc6ac7153f340f037ca795672c3b041488bc247a898bcbe7","start":617}],"trace":[]} -->
<!-- /kb:depth -->
