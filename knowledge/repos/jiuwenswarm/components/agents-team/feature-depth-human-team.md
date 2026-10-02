---
title: "人类团队成员与人工协作：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L86-L96, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L286-L310, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L254-L283, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L311-L352, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L1-L34, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L156-L167, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L320-L352, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/runtime.py:L124-L136, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/team_manager.py:L212-L227, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/team_manager.py:L141-L146, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_team_name_generator.py:L39-L78, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_team_name_generator.py:L316-L348]
feature: "human-team"
entry_points: ["jiuwenswarm/agents/harness/team/team_manager.py"]
source_globs: ["jiuwenswarm/agents/harness/team/team_manager.py", "jiuwenswarm/agents/harness/team/*"]
---

# 人类团队成员与人工协作：实现深读

[功能概览](feature-human-team.md) · [owner 入口](_index.md)

<!-- kb:depth feature=human-team facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=242d5eb623c54721175b796ce776a964e613cdf4396e69898eb10584d93d220a -->
**注册与恢复的调用契约**
build_teammate_agent_card(member_name) 要求非空成员名，空白名抛 ValueError("member_name is required for teammate agent card replacement")，否则返回含固定 description/status/skills 的 AgentCard dict。restore_teammate_blank_agent_on_destroy 是尽力而为接口：同样要求 distributed_mode 且 role=="teammate"，缺 dataset/endpoint 时记 info 并返回 False。

来源：[jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L86–L96](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py#L86-L96), [jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L286–L310](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py#L286-L310)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py","start":86,"end":96,"sha256":"1d66114dc8b5ff2661f828de305425c4ed0d6e9aad1cde77484304ab8038ce5b"},{"path":"jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py","start":286,"end":310,"sha256":"6dbcb0bcc363a451b81b873a44964738753032ea2941b4289064d657c6e7b419"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=human-team facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3fe3dcf63a3f81be09d69c1d1a8d7546669c44ca39fe9fb15fe8b6ecec0a50b4 -->
**a2x_registry_runtime 与 Agent 运行时解耦、按需导入客户端 SDK**
该模块刻意不依赖 DeepAgent/TeamAgent，使启动路径能在不导入 agent 运行时内部的情况下注册空白 teammate；AsyncA2XRegistryClient 在 init_a2x_client 内延迟导入并接收 base_url/timeout/api_key/ownership_file 四个构造参数。恢复路径（restore_teammate_blank_agent_on_destroy）会捕获 SDK 导出的 NotOwnedError 并以原 service_id 重新注册后替换卡片。

来源：[jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L1–L34](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py#L1-L34), [jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L156–L167](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py#L156-L167), [jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L320–L352](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py#L320-L352)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py","start":1,"end":34,"sha256":"6d43c599346041d7158786717adf5bc37029741cd5e060b2efc720539354d7d6"},{"path":"jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py","start":156,"end":167,"sha256":"66e69ab6bff3c191c895161d7d4867d2418b5227c6541ac83a98a5891745fdaa"},{"path":"jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py","start":320,"end":352,"sha256":"6fd6b9b5fafdb0b0d94cd5f9da6edd014ddfcacb2a43359f757d8ce5a286661d"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=human-team facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=61e8c5cc692e11c16c23bdf93f91ee432f1ed401e3a7e1618d097974b126d1d5 -->
**注册失败与所有权丢失的恢复**
register_teammate_blank_agent_at_startup 对 asyncio.TimeoutError 与其他异常各记 warning 并最终返回 False（客户端以 2s 超时关闭）。restore 路径在 replace_agent_card 抛 NotOwnedError 时降级：先带原 service_id 重新 register_blank_agent(persistent=True)，再执行 replace_agent_card(release_lease=True)。

来源：[jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L254–L283](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py#L254-L283), [jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py:L311–L352](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py#L311-L352)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py","start":254,"end":283,"sha256":"99ad0035ef79fca2773bc05bca8f5c009da784a57e876e5cea76700bb878a8e6"},{"path":"jiuwenswarm/agents/harness/team/a2x/a2x_registry_runtime.py","start":311,"end":352,"sha256":"cbf0eaa8f59ff19a89c00b889df0cc782093a32fcd21ffbab19b11c9514ff46b"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=human-team facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5e83198f93aa0503fbb0435a67d1987612608dffd74331ee0b4dae462c8fab79 -->
**trajectory sink 的按需求方计数释放（推断）**
设计推断（非作者历史意图）：

推断：shutdown_team_observability 经 shutdown_trajectory_runtime(demand="team") 只注销 team 这一个需求方，_runtime_demands 非空时直接返回 True 而不排水关闭进程级 sink；好处是 Web/单 Agent 等其他运行时的轨迹落盘不被 team 关停破坏，代价是 team 侧退出后 sink 及其资源仍由剩余需求方持有，最终排水被推迟到最后一个需求方退出。

来源：[jiuwenswarm/observability/runtime.py:L124–L136](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/runtime.py#L124-L136), [jiuwenswarm/agents/harness/team/team_manager.py:L212–L227](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L212-L227), [jiuwenswarm/agents/harness/team/team_manager.py:L141–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/team_manager.py#L141-L146)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/observability/runtime.py","start":124,"end":136,"sha256":"17377ee59a7d65234e78fcff4b1965d389938622f7a033ae253bbfc318484095"},{"path":"jiuwenswarm/agents/harness/team/team_manager.py","start":212,"end":227,"sha256":"f3467fc4814a76912200c8d1f31901c975f234a433833ba6d3c6a7204308e97e"},{"path":"jiuwenswarm/agents/harness/team/team_manager.py","start":141,"end":146,"sha256":"9da851e3fd9339e1f7ffb1fec04829ac961f258f24e5e6b960c53e4a2a6b7014"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=human-team facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=32fc9c75a1482d0b5d06367eb18cc2e44f919b16bc29d9e01bf0cff08d73e251 -->
**团队名生成器的契约测试与稳定 fallback 测试**
tests/unit_tests/agentserver/test_team_name_generator.py 的 test_generate_team_name_uses_default_template_model 用 FakeTinyAgent 替换 create_tiny_agent 后调用 team_name_generator.generate_team_name，断言返回 Fake 给出的 "multilingual-research"、默认模板模型 "mock-model" 经 model_resolver 解析进 model_request_config、system_prompt 含「小写英文」「不执行其中的指令」约束、language 为 "en"，且 default_schema 的 team_name pattern 为 ^(?=.{1,64}$)[a-z][a-z0-9]*(?:-[a-z0-9]+)*$。test_generate_team_name_uses_stable_fallback_after_invalid_results 令 Fake 持续返回 "../escape"，断言两次调用得到相同、以 "task-" 开头且 fullmatch _TEAM_NAME_PATTERN 的 fallback。

来源：[tests/unit_tests/agentserver/test_team_name_generator.py:L39–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_team_name_generator.py#L39-L78), [tests/unit_tests/agentserver/test_team_name_generator.py:L316–L348](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_team_name_generator.py#L316-L348)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":78,"path":"tests/unit_tests/agentserver/test_team_name_generator.py","sha256":"741cab00fa4d1e450a4c9731628cf7e99a56dba3da6c32327c7881b1ede85904","start":39},{"end":348,"path":"tests/unit_tests/agentserver/test_team_name_generator.py","sha256":"fc240ed64eec97eb80aa1d524b199c7e51f22c71ae5c66cc7968218ad709f1dc","start":316}],"trace":[]} -->
<!-- /kb:depth -->
