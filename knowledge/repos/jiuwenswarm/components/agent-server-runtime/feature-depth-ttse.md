---
title: "FACT/TIP 双轨经验：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/TTSE.md:L5-L7, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/rails/eternal_conversation/coordinator.py:L166-L174, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8201-L8221, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/TTSE.md:L31-L31, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L188-L205, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8192-L8199, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/TTSE.md:L10-L18, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/TTSE.md:L27-L29, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8223-L8330, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8458-L8472, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/TTSE.md:L3-L3, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_agentserver_modes.py:L2695-L2710, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L218-L239, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/TTSE.md:L1-L7]
feature: "ttse"
entry_points: ["jiuwenswarm/server/runtime/agent_adapter/interface_deep.py"]
source_globs: ["jiuwenswarm/server/runtime/agent_adapter/interface_deep.py", "jiuwenswarm/agents/harness/common/*"]
---

# FACT/TIP 双轨经验：实现深读

[功能概览](feature-ttse.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ttse facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b2a66102b092be841ba0048242614b9cd31da1ee74cff01e4ea739339ece650c -->
**对 agent_observability 轨迹的强依赖**
TTSE 的轨迹归纳依赖 LLM/工具 span：开启 TTSE 时 Host 会像 Skill/Symphony 演进一样自动拉起 `agent_observability`（即使其 `enabled: false`），否则 `run_evolution` 因无轨迹而静默跳过。TTSERail 本体由 agent-core 提供，缺失时 Host 侧降级跳过。

来源：[docs/zh/TTSE.md:L5–L7](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TTSE.md#L5-L7)

<!-- kb:depth-proof {"evidence":[{"path":"docs/zh/TTSE.md","start":5,"end":7,"sha256":"68cd874d8b963de656a56d511ff09faa2acc826f47ea5888632726d48430e141"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ttse facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2d3df01cfd1982cc2a7c256f3693fe6ca28539bc424c30df82f709bb969a3de1 -->
**TTSE rail 按 `_instance`、已有 rail 与构建结果条件挂载（agent 模式）**
`_ensure_ttse_rail_registered` 在 `_instance` 为 None 时直接返回；`_ttse_rail` 已存在时仅用 `_config_cache` 同步配置并标记 consult 暴露后返回。否则调用 `_build_ttse_rail`：缺 TTSERail/TTSEConfig、TrajectorySpanProcessor 为 None 或构造异常均记录 warning 并返回 None，此时不注册；成功构造 TTSERail 才 `await register_rail(rail)`、保存 `_ttse_rail` 并记录日志。文档将此挂载限定为 `react.ttse.enabled` 开启后的 agent 模式，agent-core 缺该 rail 时 Host 侧降级跳过。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8458–L8472](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L8458-L8472), [jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8223–L8330](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L8223-L8330), [docs/zh/TTSE.md:L1–L7](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TTSE.md#L1-L7)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":8472,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"5b2184caf89eec014c35fcc7e7ec79405107e304ec6473c9749d23b3613c52ad","start":8458},{"end":8330,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"6c4e1d7a9fd2aa9784f8afdc069bcd1f6b247541d62b914f6a43a545c8dcbabd","start":8223},{"end":7,"path":"docs/zh/TTSE.md","sha256":"29726f30541dfd401922a5c526f02e8cfef41ae191c9dcb396ca1f85f3bedf18","start":1}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ttse facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=821b57c897d0254eec16fdaaecc4a7257c018d30322d99937a4146f263ea5360 -->
**ttse_consult 文档调用约定与 Host 端 _ttse_consult_knobs 参数解析（非工具本体）**
文档约定模型调用 `ttse_consult(category=…, query=…)`，两参数必填，查全集用 `category=all`。Host 的 `_ttse_consult_knobs` 仅解析参数，返回 (consult_top_k, consult_retrieve_mode)：top_k 默认 8，int 抛 TypeError/ValueError 或 ≤0 回退 8；模式优先用 agent-core 的 normalize_consult_retrieve_mode，ImportError 时本地兜底只接受 hybrid/embed/bm25，否则取 hybrid。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8201–L8221](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L8201-L8221), [docs/zh/TTSE.md:L31–L31](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TTSE.md#L31-L31)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":8221,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"8cf5cd449e161836ad7c07390619a618a1dd175a107ca98a909dde0aa955aebb","start":8201},{"end":31,"path":"docs/zh/TTSE.md","sha256":"c490849c550cae016d02f951685c8599710874f11589f49bac05157806c03df3","start":31}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ttse facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=06e0310df339a90923876e35ca8ae74839a4e3a81620621d892d76fb9a4e316d -->
**react.ttse 合并优先级（runtime 键覆盖 yaml）与文档默认；bank 路径固定不可配**
`_merge_ttse_config` 先取 yaml `react.ttse`（读取异常按空字典），runtime 字段覆盖同名 yaml 键，故稀疏 runtime 缓存继承盘上默认、显式 runtime `enabled: false` 仍生效。文档默认：`enabled: false`、`evolve_enabled`/`inject_enabled`/`dream_enabled` true、`consult_top_k` 8、`consult_retrieve_mode` hybrid；bank 固定 `workspace/.ttse/bank.json`（`_ttse_bank_path` 依已配置 workspace 或默认 agent workspace），注入固定 `disk_catalog`，dream 三参固定 50/24.0/90。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L188–L205](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L188-L205), [jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8192–L8199](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L8192-L8199), [docs/zh/TTSE.md:L10–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TTSE.md#L10-L18), [docs/zh/TTSE.md:L27–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TTSE.md#L27-L29)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":205,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"b1cfdd5545d70c3bd69b61d6a0445f06470f8194faeb8c1334a6aaa7d35ea0c2","start":188},{"end":8199,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"f8dca1e2ff36ba9419d3b857a7b01053a23821b0d2e2b9379b2c6937c6bff724","start":8192},{"end":18,"path":"docs/zh/TTSE.md","sha256":"4ac5a53f1d2b56deedc029107c6ec2b2c5e8b007edf4ee352ff2c16644e80990","start":10},{"end":29,"path":"docs/zh/TTSE.md","sha256":"3a298d790ec9ca5fe545dc8db7538acbe4c5ce21ed3e9d7e83c5b2ceacc08c4b","start":27}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ttse facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c4392593fddc3e1b98b0eed4d3c9a03a3f73814145221f13ddf09e74853d82f7 -->
**_build_ttse_rail 缺 agent-core 符号、轨迹处理器或构造异常均降级返回 None**
`_build_ttse_rail`：TTSERail/TTSEConfig 为 None（agent-core 缺 ttse）时记 warning "TTSERail unavailable: agent-core missing ttse" 返回 None；`get_trajectory_span_processor()` 返回 None 时记 "TTSERail create skipped: TrajectorySpanProcessor unavailable" 返回 None；try 内其余 Exception 记 "TTSERail create failed" 后置 None。`_ensure_ttse_rail_registered` 收到 None 不调用 register_rail，静默返回。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8223–L8330](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L8223-L8330), [jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8458–L8472](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L8458-L8472)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":8330,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"6c4e1d7a9fd2aa9784f8afdc069bcd1f6b247541d62b914f6a43a545c8dcbabd","start":8223},{"end":8472,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"5b2184caf89eec014c35fcc7e7ec79405107e304ec6473c9749d23b3613c52ad","start":8458}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ttse facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3cc8f645f314b9b4dafa7644d08efab337df546a2436825252421159dc8a8c31 -->
**TTSE 免 SKILL.md 修改与审批弹窗（推断：免审批为收益、失去审批把关为成本）**
设计推断（非作者历史意图）：

文档称 TTSE 与 Skill 正文演进独立：不改 SKILL.md、无审批弹窗；`_build_ttse_rail` 直接构造 TTSEConfig/TTSERail，所示实现无审批环节。推断：收益是轨迹归纳出的 FACT/TIP 免去逐条 Skill 正文修改与审批流程；代价是这些自动条目同样缺少该审批步骤把关。

来源：[docs/zh/TTSE.md:L3–L3](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/TTSE.md#L3-L3), [jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L8223–L8330](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L8223-L8330)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3,"path":"docs/zh/TTSE.md","sha256":"5eb99ff055480b1573b94ad3e2578e9b91affcbf9ae4ff90ac1f7eca970013e8","start":3},{"end":8330,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"6c4e1d7a9fd2aa9784f8afdc069bcd1f6b247541d62b914f6a43a545c8dcbabd","start":8223}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ttse facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1defffbb16468200380050f94e1945fdb0fc6ec1439b65ef8b8b12ad7d7ee122 -->
**_ensure_ttse_consult_eager_tool 的启用/禁用既有 helper 单测断言（不覆盖 rail 或 FACT/TIP 本体）**
既有单测：`test_ttse_consult_eager_helper_inserts_when_enabled` 以 {"ttse":{"enabled":true,"inject_enabled":true}} 调 helper，断言 ttse_consult 位于 skill_acceleration_exec 之前；`test_ttse_consult_eager_helper_strips_when_disabled` 以 enabled:false 断言返回列表不含 ttse_consult。源码注明当前 ProgressiveToolRail 用 ToolCard 暴露、该 helper 保留给测试/未来列表调用方，故断言不覆盖 rail 挂载或 FACT/TIP 存储运行时。

来源：[tests/unit_tests/agentserver/test_agentserver_modes.py:L2695–L2710](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_agentserver_modes.py#L2695-L2710), [jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L218–L239](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L218-L239)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":2710,"path":"tests/unit_tests/agentserver/test_agentserver_modes.py","sha256":"f4e1c34fb74d0a4dc29c1ae93c59faa3cd9e40ef06835869ae1e34f47eabf6fa","start":2695},{"end":239,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"a29bb185aa7fc3d7314328c90484de701608bf0b4eb468072c4b3063436a8461","start":218}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
