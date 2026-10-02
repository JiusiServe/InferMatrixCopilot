---
title: "SwarmFlow 工作流与 HITL：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/workflow_state.py:L832-L847, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py:L75-L102, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py:L173-L187, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_workflow_monitor_handler.py:L617-L679, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/TUI使用SwarmFlow指南.md:L217-L228", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py:L17-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/base_monitor_handler.py:L52-L57, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/workflow_state.py:L284-L289, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/workflow_state.py:L432-L442, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/workflow_state.py:L1627-L1640, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py:L193-L195]
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

<!-- kb:depth feature=swarmflow facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6825f14fb36947a3c84acd31941986e12d4b666dd7a8c0d04c6308691ab52815 -->
**WorkflowRunState.apply 按 progress.kind 分发，未命中 _KIND_HANDLERS 即返回 None（无需推送）**
类文档声明 WorkflowRunState 维护聚合状态：apply(progress)->delta 供增量推送，to_workflow_run_dict() 供全量快照。apply 取 progress.kind 在 _KIND_HANDLERS 查 handler：未命中直接 return None（文档注明 log 或未知 kind 无需推送）；命中则经 getattr 调用该 handler 方法，其返回值即增量 delta dict。

来源：[jiuwenswarm/agents/harness/team/handlers/workflow_state.py:L284–L289](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/workflow_state.py#L284-L289), [jiuwenswarm/agents/harness/team/handlers/workflow_state.py:L432–L442](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/workflow_state.py#L432-L442)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":289,"path":"jiuwenswarm/agents/harness/team/handlers/workflow_state.py","sha256":"674972fd5ce3bfcc2850a31b3fb884ef0d0844e2e2c476a8c3b99016f8832882","start":284},{"end":442,"path":"jiuwenswarm/agents/harness/team/handlers/workflow_state.py","sha256":"3c4a20373fd9264695b93bd4c5a73963bcd0c127f73d5033e256ac0bf69681c9","start":432}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=swarmflow facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f665d3fd4201a0f49486e6a0e22ad21252faf412ddc8f0b60a696748b58ea043 -->
**to_workflow_run_dict 供 command.workflows 全量快照（文档声明），get_workflow_snapshot 逐 run 调用**
文档串声明其返回完整 WorkflowRun dict 用于 command.workflows 快照：结构对齐 workflow.updated 事件的 workflow 字段，但含全部 phases 与全部 agents（非增量）。实现先调 _refresh_run_agent_counts()，再以 id、name、summary、status、agent_count、completed_agent_count 构造结果 dict；调用方 get_workflow_snapshot 遍历 _runs.values() 逐 run 调用它并返回列表。

来源：[jiuwenswarm/agents/harness/team/handlers/workflow_state.py:L1627–L1640](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/workflow_state.py#L1627-L1640), [jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py:L193–L195](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py#L193-L195)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1640,"path":"jiuwenswarm/agents/harness/team/handlers/workflow_state.py","sha256":"d7bbe066c3252f1c92a42672edd9a7b21e8686249d86420b2e370785a518f664","start":1627},{"end":195,"path":"jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py","sha256":"44ea200909877420c0358a0251b24e2656e63836e251ef35dee3a636324da7cc","start":193}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=swarmflow facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2b82676e822a3514597e9c8bfa766eb162b6b367383cec9b0027eb9918aa5a34 -->
**enable_swarmflow 配置与 /swarmflow on 的 session 生效边界**
文档规定：`/mode team` 仅切模式，配置 `enable_swarmflow: false` 时 Leader 不会跑 SwarmFlow；`/swarmflow on` 推荐使用，一次完成开 SwarmFlow 并进 team，写配置后「下次」workflow run 才可见监控；已在 team 且开关 off 时，当前 session 的 monitor 可能未补建，执行 `/new` 后立刻生效。

来源：[docs/zh/TUI使用SwarmFlow指南.md:L217–L228](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TUI%E4%BD%BF%E7%94%A8SwarmFlow%E6%8C%87%E5%8D%97.md#L217-L228)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":228,"path":"docs/zh/TUI使用SwarmFlow指南.md","sha256":"9e3dcb07840da356ca3a66bb77ef41d2a34757b7007657223f3b13e37fe8f2b5","start":217}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=swarmflow facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7b0fad67853e0e433af23534eca78e1e9a4efbc65767d879a38bcf56ac374950 -->
**依赖 openjiuwen SDK 的 TeamMonitor 事件源；丢弃队列项需补 task_done() 维持 join() 计账**
WorkflowMonitorHandler 从 SDK `openjiuwen.agent_teams.monitor.team_monitor` 导入 TeamMonitor 作为事件源，并把状态维护交给本地 WorkflowRunState/WorkflowProgress。DropOldestQueue._discard_queued_item 删除队首项并 dropped_count+=1 后补调 task_done()——注释说明被丢弃项永远收不到 task_done()，以此保持 asyncio.Queue 计账对使用 join() 的调用方正确。

来源：[jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py:L17–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py#L17-L22), [jiuwenswarm/agents/harness/team/handlers/base_monitor_handler.py:L52–L57](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/handlers/base_monitor_handler.py#L52-L57)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":22,"path":"jiuwenswarm/agents/harness/team/handlers/workflow_monitor_handler.py","sha256":"674533bb5bb2fcbb1c09fa3389a5d7cf7365d1a98d94d3d8f4a198d784f18480","start":17},{"end":57,"path":"jiuwenswarm/agents/harness/team/handlers/base_monitor_handler.py","sha256":"97e4363c3880cf9e9fd0485800d432adb4b1f429ba8dcc4759d08898f129a459","start":52}],"trace":[]} -->
<!-- /kb:depth -->
