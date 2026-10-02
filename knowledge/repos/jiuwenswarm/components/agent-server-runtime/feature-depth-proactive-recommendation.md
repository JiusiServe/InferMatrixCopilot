---
title: "主动推荐、频率限制与主 Agent 交付：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/proactive_adapter.py:L393-L451, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/proactive_adapter.py:L85-L117, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/recommendation/proactive_actions.py:L235-L269, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L34-L36, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/recommendation/proactive_engine.py:L78-L161, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/设置与频道升级迁移指南.md:L183-L188"]
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
