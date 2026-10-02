---
title: "多智能体团队协作：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/team_manager.py:L130-L209, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/config.py:L299-L301, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/config.py:L112-L154, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/team_manager.py:L212-L227, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/runtime.py:L124-L136, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/team_manager.py:L178-L209, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L254-L283, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/team_manager.py:L141-L144, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/team_manager.py:L212-L219, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/runtime.py:L130-L136, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_team_runtime_inheritance.py:L168-L181]
feature: "team"
entry_points: ["jiuwenswarm/agents/harness/team/team_manager.py"]
source_globs: ["jiuwenswarm/agents/harness/team/team_manager.py", "jiuwenswarm/agents/harness/team/*.py"]
---

# 多智能体团队协作：实现深读

[功能概览](feature-team.md) · [owner 入口](_index.md)

<!-- kb:depth feature=team facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d449980d2c47d842ee6a80718e2a33d26ca9e21b05a172b65380c48cedb17b5a -->
**team_observability 与 trajectory_ui 的默认值与联动**
team_observability.enabled 默认 False，但只要 trajectory_ui.enabled 为真或 skill/symphony evolution 开启（get_skill_evolution_enabled 严格判定 react.evolution.skill_evolution is True），provider 就会被拉起；traces_dir 缺省为用户工作区下的 .trace 目录。trajectory_ui 各数值字段走保守默认（如 enabled 默认 False），老配置缺该节时数据面保持关闭。

来源：[jiuwenswarm/agents/harness/team/team_manager.py:L130–L209](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L130-L209), [jiuwenswarm/common/config.py:L299–L301](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L299-L301), [jiuwenswarm/observability/config.py:L112–L154](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/config.py#L112-L154)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/team/team_manager.py","start":130,"end":209,"sha256":"c4dd83322dc2b603243de91b5b4b3932932b4477c3f502b55b6191e5fe685f1e"},{"path":"jiuwenswarm/common/config.py","start":299,"end":301,"sha256":"8e4b40d75172c3f84f976d6184d6ebec62914d205d81fa6288738b8a3dc21f46"},{"path":"jiuwenswarm/observability/config.py","start":112,"end":154,"sha256":"c0c1e8b9398da6a44f8036f9cc0dd40f195401b978ae41100a7d2f61182fd990"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=team facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c51a2b8e45493d4547ddbc61c59a786b5451663ffa8bc7cbaa8ea8e8984687c5 -->
**对进程级 trajectory 运行时的按需求引用计数**
团队观测与单 Agent 共享同一个进程级 trajectory sink：shutdown_team_observability 以 demand="team" 调 shutdown_trajectory_runtime，后者先从 _runtime_demands 移除该 demand，若仍有其他需求方则直接返回 True 不排空 sink。这保证 Team 关闭观测不会拆掉其他运行时仍在使用的轨迹落盘通道。

来源：[jiuwenswarm/agents/harness/team/team_manager.py:L212–L227](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L212-L227), [jiuwenswarm/observability/runtime.py:L124–L136](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/runtime.py#L124-L136)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/team/team_manager.py","start":212,"end":227,"sha256":"f3467fc4814a76912200c8d1f31901c975f234a433833ba6d3c6a7204308e97e"},{"path":"jiuwenswarm/observability/runtime.py","start":124,"end":136,"sha256":"17377ee59a7d65234e78fcff4b1965d389938622f7a033ae253bbfc318484095"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=team facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=99a9394f0e328e62e5c5226f5dc6e7b03c261be909d090994d15b5064c725662 -->
**观测初始化失败与空白注册失败的传播差异**
sync_team_observability 初始化失败时：若 evolution 请求了 provider，则抛 RuntimeError("Team evolution observability initialization failed") 阻断；否则仅记 warning 并把 _observability_active 置 False 降级继续。启动期 A2X 空白注册对超时/异常一律 best-effort：记 warning 后返回 False，且 finally 中关闭客户端也再包一层 2 秒超时。

来源：[jiuwenswarm/agents/harness/team/team_manager.py:L178–L209](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L178-L209), [jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L254–L283](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py#L254-L283)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/team/team_manager.py","start":178,"end":209,"sha256":"6e4be0ce367bdade68a04843fbb2c9e4b376bde490a2961eec56cbba8149b321"},{"path":"jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py","start":254,"end":283,"sha256":"99ad0035ef79fca2773bc05bca8f5c009da784a57e876e5cea76700bb878a8e6"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=team facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f8fc1a26bcd5afecf4a468b7d0d5c632abe3dd5f0d7ae576ba4a2a495706af4b -->
**轨迹 sink 的 demand 引用计数：跨运行时共存收益，代价是 drain 推迟到无人持有 demand**
选择：进程级轨迹 sink 按 demand 计数共享，shutdown_team_observability 以 demand="team" 调用 shutdown_trajectory_runtime（216），后者 discard 该 demand 后若 _runtime_demands 仍非空直接 return True 而不 drain，只有最后一个 demand 释放才走 _shutdown_locked（observability/runtime.py 130–136）。收益（docstring 写明）：Team tracing 保留自己的 demand，禁用 Team 观测不会拆掉其他运行时仍在用的轨迹 sink（141–144）；代价：真正的 drain 与关闭被推迟到没有任何 demand 持有为止。

来源：[jiuwenswarm/agents/harness/team/team_manager.py:L141–L144](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L141-L144), [jiuwenswarm/agents/harness/team/team_manager.py:L212–L219](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L212-L219), [jiuwenswarm/observability/runtime.py:L130–L136](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/runtime.py#L130-L136)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":144,"path":"jiuwenswarm/agents/harness/team/team_manager.py","sha256":"689ba12e360be661aa202186a672304d0b97310be6834cec3d93b04d711f0907","start":141},{"end":219,"path":"jiuwenswarm/agents/harness/team/team_manager.py","sha256":"5bab61b948745448c75072f5315bc427a5aec7b0937b19878cb6e63979ac630f","start":212},{"end":136,"path":"jiuwenswarm/observability/runtime.py","sha256":"aa1fff1d976afcdb5beddbd083e49e528771895ac479bc8ad7c7fcd57747f3e4","start":130}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=team facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7f21b5b2a66f65da1574d724c61594613ef65611b6b96dc664a817c496a8d04b -->
**test_build_member_rails_omits_task_planning_for_leader_only：断言成员 rail 按角色分化**
pytest 入口 tests/unit_tests/agentserver/test_team_runtime_inheritance.py::test_build_member_rails_omits_task_planning_for_leader_only（168–181）分别以 role="leader" 与 role="teammate"、runtime=RuntimeInfo(language="cn") 调用 build_member_rails 两次，断言 leader 的 rails 中不存在 TaskPlanningRail 而 teammate 的存在，且两者均不含 HeartbeatRail——检验成员 rail 装配的角色分化行为。此处仅陈述测试断言内容，不声明这些测试当前已运行通过。

来源：[tests/unit_tests/agentserver/test_team_runtime_inheritance.py:L168–L181](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_team_runtime_inheritance.py#L168-L181)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":181,"path":"tests/unit_tests/agentserver/test_team_runtime_inheritance.py","sha256":"6a3c580622f358f5cc3377ab75d70a93852e922de7af200c54de940978802610","start":168}],"trace":[]} -->
<!-- /kb:depth -->
