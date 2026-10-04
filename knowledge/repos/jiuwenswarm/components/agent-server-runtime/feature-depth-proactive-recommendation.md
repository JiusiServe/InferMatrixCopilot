---
title: "主动推荐、频率限制与主 Agent 交付：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/proactive_adapter.py:L393-L451, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/proactive_adapter.py:L85-L117, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/recommendation/proactive_actions.py:L235-L269, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L34-L36, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L78-L161, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/设置与频道升级迁移指南.md:L183-L188", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/proactive_adapter.py:L92-L103, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L301-L304, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_proactive_adapter_runtime_boundary.py:L36-L39, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/proactive_adapter.py:L86-L98, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L163-L188, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L423-L434, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/proactive_adapter.py:L97-L117, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/symphony/test_proactive_recommendation_flow.py:L401-L420, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/symphony/test_proactive_recommendation_flow.py:L423-L435]
feature: "proactive-recommendation"
entry_points: ["jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py", "jiuwenswarm/server/runtime/proactive_adapter.py"]
source_globs: ["jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py", "jiuwenswarm/server/runtime/proactive_adapter.py"]
---

# 主动推荐、频率限制与主 Agent 交付：实现深读

[功能概览](feature-proactive-recommendation.md) · [owner 入口](_index.md)

<!-- kb:depth feature=proactive-recommendation facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e3c837e8c0b72780a8e5279b1f13b5fdffa56bfcd5cbd7b0394febf6416daac7 -->
**启动装配链：init_proactive_engine → build_proactive_agent → _get_model**
AgentServer 启动时 init_proactive_engine(server, config) 构造 ProactiveEngine，随后直接调用 build_proactive_agent()；后者再调用 proactive_actions._get_model(temperature=0.0) 取默认模型并禁用 thinking，最后用该模型 create_deep_agent 生成无工具、单轮的决策专用 agent，经 set_proactive_agent 注入引擎并挂到 server 上。

调用路径：`jiuwenswarm/server/runtime/proactive_adapter.py`（`init_proactive_engine`） → `jiuwenswarm/server/runtime/proactive_adapter.py`（`build_proactive_agent`） → `jiuwenswarm/agents/harness/common/recommendation/proactive_actions.py`（`_get_model`）

来源：[jiuwenswarm/server/runtime/proactive_adapter.py:L393–L451](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/proactive_adapter.py#L393-L451), [jiuwenswarm/server/runtime/proactive_adapter.py:L85–L117](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/proactive_adapter.py#L85-L117), [jiuwenswarm/agents/harness/common/recommendation/proactive_actions.py:L235–L269](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/recommendation/proactive_actions.py#L235-L269)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/proactive_adapter.py","start":393,"end":451,"sha256":"9cf1c0a9e9cb4c52002a1674fcc21953abc6c1d2275ac74e2f76c4723e158ab9"},{"path":"jiuwenswarm/server/runtime/proactive_adapter.py","start":85,"end":117,"sha256":"a99aecfe922750727c7f052f88da82040dbfc23d78a7bc27eb19d7ce6bb5f47c"},{"path":"jiuwenswarm/agents/harness/common/recommendation/proactive_actions.py","start":235,"end":269,"sha256":"5d506c1ffb7a8fe33dcdfa9a13d61249916c70457bda34c540866c437e5eb2ad"}],"trace":[{"path":"jiuwenswarm/server/runtime/proactive_adapter.py","symbol":"init_proactive_engine","start":393,"end":451},{"path":"jiuwenswarm/server/runtime/proactive_adapter.py","symbol":"build_proactive_agent","start":85,"end":117},{"path":"jiuwenswarm/agents/harness/common/recommendation/proactive_actions.py","symbol":"_get_model","start":235,"end":269}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=proactive-recommendation facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=600e45e7ac02d38d233deecac7adb3a5959123b39eebfb6ef45814ddb1abc64d -->
**proactive 数值与开关的默认值及合法区间**
ProactiveEngine.__init__ 读取 enabled（默认 False，防御性默认=关闭，配置段缺失时不会误启用）、max_recommend_per_day（默认 5）、max_rounds_per_tick（默认 20），数值经 _safe_proactive_int 校验，合法区间为 1–50（_PROACTIVE_INT_LO/_PROACTIVE_INT_HI）；前端这两个数值位于"推荐频率限制"弹窗，同样限 1–50 整数。reload_config 热更新时当日计数 _daily_counts 不重置，以保持上限语义。

来源：[jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L34–L36](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py#L34-L36), [jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L78–L161](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py#L78-L161), [docs/zh/设置与频道升级迁移指南.md:L183–L188](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E8%AE%BE%E7%BD%AE%E4%B8%8E%E9%A2%91%E9%81%93%E5%8D%87%E7%BA%A7%E8%BF%81%E7%A7%BB%E6%8C%87%E5%8D%97.md#L183-L188)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py","start":34,"end":36,"sha256":"909a823d15c72c82105baaadb80fbf56eb9d8c5dd4d86b109b96ab41122ce3b4"},{"path":"jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py","start":78,"end":161,"sha256":"91c31c5b81f45366d4804de554e9b2f19ec7461d7170c1a47d547832e4590e9b"},{"path":"docs/zh/设置与频道升级迁移指南.md","start":183,"end":188,"sha256":"4ae3994097bbb075058c3372989a9b6a9debda89ec8327d4ebacf8c1461c7bfa"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=proactive-recommendation facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=24f1ce1d4e5edbc388fa988f5167d79f02f13aedb18c2698343acf3571c3405d -->
**tick_now 契约：enabled 为假即 False；异常转 False；_tick 触发成功立即返回 True**
对外入口 `tick_now(target_channel=None) -> bool`（docstring 称供 CronScheduler/手动触发）：`enabled` 为假→debug 日志+return False；否则 `bool(await self._tick(...))`，任何 Exception→warning+False。`_tick` 尾部：`triggered` 为假→info 日志、更新 `_last_tick_at`、False；为真→立即 return True（注释称 fire-and-forget，计数由 `_on_delivered` 回调完成）。

来源：[jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L163–L188](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py#L163-L188), [jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L423–L434](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py#L423-L434)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":188,"path":"jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py","sha256":"271b3efea930c0970c0dacc19a9c3b3720f2e616441bb1a6c7696bdcd092b13d","start":163},{"end":434,"path":"jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py","sha256":"65c8ecc1ccec8f539c885310fdc585c7d90378446eb668f6efbb6441acd1ef8f","start":423}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=proactive-recommendation facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8c593a4ebf3011915b74bb5405b2bfd170e17e0b350ba26ef379f7cedf724de9 -->
**依赖 proactive_actions._get_model 与 openjiuwen 工厂；ImportError 降级为 None，且测试禁止耦合 agent_ws_server**
决策 agent 复用 proactive_actions._get_model，经 openjiuwen 的 create_deep_agent/AgentCard 构建；ImportError 时记 warning 返回 None，tick 因无 agent 直接返回 False。另有测试断言本模块源码文本不含 jiuwenswarm.server.agent_ws_server 与 WebSocketGatewayPushTransport。

来源：[jiuwenswarm/server/runtime/proactive_adapter.py:L92–L103](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/proactive_adapter.py#L92-L103), [jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L301–L304](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py#L301-L304), [tests/unit_tests/agentserver/test_proactive_adapter_runtime_boundary.py:L36–L39](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_proactive_adapter_runtime_boundary.py#L36-L39)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":103,"path":"jiuwenswarm/server/runtime/proactive_adapter.py","sha256":"bed7efc45a3d637748e30c8f39e34f47d36437e1cefe83f72179b848960ca11a","start":92},{"end":304,"path":"jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py","sha256":"61e40ac40878e8e2255c36a1ec45e0f7d5de8c4068103279c53c4e6b01dad810","start":301},{"end":39,"path":"tests/unit_tests/agentserver/test_proactive_adapter_runtime_boundary.py","sha256":"b398e62af92232cee4499438b60a3aaffc9911a843e9bd2d2b4522346355fc01","start":36}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=proactive-recommendation facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=70e871061d1a1dc7d6f3b86da070f6a62c679b4f9368c0ff3edcf55bd421d4c6 -->
**init_proactive_engine 捕获初始化异常不重抛；agent 构建失败降级为 None 且仍传入引擎**
`init_proactive_engine` 的 try（引擎构建至 449 `server.set_proactive_engine`）内任何 Exception 在 450-451 被捕获：记 warning、不再抛出；若发生在 449 之前，引擎不会被挂到 server。agent 构建侧已示分支在 import 失败、`_get_model` 返回 None（无模型）或 `create_deep_agent` 异常时记 warning 并 return None，而 406-407 仍把该结果传给 `set_proactive_agent`。

来源：[jiuwenswarm/server/runtime/proactive_adapter.py:L393–L451](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/proactive_adapter.py#L393-L451), [jiuwenswarm/server/runtime/proactive_adapter.py:L97–L117](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/proactive_adapter.py#L97-L117)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":451,"path":"jiuwenswarm/server/runtime/proactive_adapter.py","sha256":"9cf1c0a9e9cb4c52002a1674fcc21953abc6c1d2275ac74e2f76c4723e158ab9","start":393},{"end":117,"path":"jiuwenswarm/server/runtime/proactive_adapter.py","sha256":"577b2c5bded9efb06c14872f27d9a9c0e2241455c6e6eb7b56e0952e131854ad","start":97}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=proactive-recommendation facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8de1e03e443386d9de2036aff593c74f2b3466f3de06a2fc5f3389c9153381e5 -->
**决策改走 agent 框架 invoke 链路换取 rails/模型选择/观测（docstring 自述），推断代价为 openjiuwen 导入失败即停摆**
设计推断（非作者历史意图）：

收益（docstring 自述）：替代裸 model.invoke，走 agent 框架 invoke 链路获得 rails/模型选择/观测；推断代价：新增 openjiuwen 导入链，ImportError 时决策 agent 为 None、tick 直接跳过。

来源：[jiuwenswarm/server/runtime/proactive_adapter.py:L86–L98](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/proactive_adapter.py#L86-L98), [jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L301–L304](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py#L301-L304)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":98,"path":"jiuwenswarm/server/runtime/proactive_adapter.py","sha256":"530c8caeadebfef1033ea89db04e81809ce1bc2314e482a52d8b8c67a3cd0b05","start":86},{"end":304,"path":"jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py","sha256":"61e40ac40878e8e2255c36a1ec45e0f7d5de8c4068103279c53c4e6b01dad810","start":301}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=proactive-recommendation facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1a22e250e0ead34a0f5c0aac3b464d6a4e46028153f3d1bc0e49f28ca4b23134 -->
**决策解析 helper 的直调异步测试断言（仅覆盖 _analyze_and_decide，非引擎全链路）**
两个 `@pytest.mark.asyncio` 测试直接 await 真实 `_analyze_and_decide`：mock 专用 agent 返回 JSON 时断言 `result.decision.type == "skill_recommend"`、target 与 urgency 0.7（415-420）；agent 返回非 JSON（"这不是JSON"）时断言 `result.decision is None`（434-435）。断言只覆盖该决策解析 helper；所示行未断言引擎 tick/主 Agent 交付链路。未执行，仅引用既有测试行。

来源：[tests/symphony/test_proactive_recommendation_flow.py:L401–L420](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/symphony/test_proactive_recommendation_flow.py#L401-L420), [tests/symphony/test_proactive_recommendation_flow.py:L423–L435](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/symphony/test_proactive_recommendation_flow.py#L423-L435)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":420,"path":"tests/symphony/test_proactive_recommendation_flow.py","sha256":"3d206ae008d0649ee186523dac511a277c700f2671c2f668952b21c04398485f","start":401},{"end":435,"path":"tests/symphony/test_proactive_recommendation_flow.py","sha256":"e5d5d6c6b4a1a62c3a0e1181bb7d1fefedb46808e6c45aea1a38e3002419803b","start":423}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
