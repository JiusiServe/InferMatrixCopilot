---
title: "长期记忆：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/config.py:L250-L281, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/config.py:L207-L247, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py:L51-L71, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L37-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L49-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L82-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/memory/test_external_memory_builder.py:L285-L290, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/memory/test_external_memory_config.py:L117-L126, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/memory/test_external_memory_builder.py:L519-L524, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py:L133-L155, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py:L160-L179, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py:L206-L219, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L30-L49, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/manager.py:L878-L889, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/manager.py:L890-L942, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/manager.py:L944-L954, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/manager.py:L895-L925]
feature: "memory"
entry_points: ["jiuwenswarm/agents/harness/common/memory/manager.py"]
source_globs: ["jiuwenswarm/agents/harness/common/memory/manager.py", "jiuwenswarm/agents/harness/common/memory/*"]
---

# 长期记忆：实现深读

[功能概览](feature-memory.md) · [owner 入口](_index.md)

<!-- kb:depth feature=memory facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=77b957382daa83913df3464e57995d0a0eca0feaf568ffd554aaab09febd8d6e -->
**记忆开关的模式相关默认值**
is_memory_enabled(mode) 经 _resolve_mode_memory 归一 mode 后读 modes.agent.memory.enabled 或 modes.code.memory.enabled：code 族（含 code.*、agent.code.*、team.code.*，判定复用 mode_matrix.is_code_profile_mode）缺省 enabled=True，agent 族缺省 False；配置读取抛异常时记 warning 并返回 False。另 DreamingConfig.load 中，环境变量 DREAMING_{MODE}_ENABLED 优先于 config.yaml 的 memory.dreaming.{mode}.enabled（默认 false），间隔默认 14400.0 秒且可被 DREAMING_INTERVAL 覆盖。

来源：[jiuwenswarm/agents/harness/common/memory/config.py:L250–L281](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/config.py#L250-L281), [jiuwenswarm/agents/harness/common/memory/config.py:L207–L247](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/config.py#L207-L247), [jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py:L51–L71](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py#L51-L71)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/memory/config.py","start":250,"end":281,"sha256":"d0cf034249e3b6c660c35aeb9beb5fe3ce2aed6efd9adab36b125f4a3a760e74"},{"path":"jiuwenswarm/agents/harness/common/memory/config.py","start":207,"end":247,"sha256":"6a37a7a8a0f8b8979e9cfe0d146e7714c6128b3731291ab3f1f9999dcfd70538"},{"path":"jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py","start":51,"end":71,"sha256":"0d1637e0457ea0e80a363ed5e0385c45a806408d4a51a0e3c5961e2b4262ee87"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=memory facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c821c5498f347784655d02d8f6e1c8b1f65848d83694b62981d30ba5c9168352 -->
**build_external_memory_rail 的返回契约与调用方门控义务**
契约：输入 config 字典（第 42 行 get_external_memory_config(config)），返回 ExternalMemoryRail 或 None——rail 导入失败记 warning 返回 None（37-40），provider 名为空返回 None（44-45），按 provider 名分发到 _build_openjiuwen/_build_mem0/_build_openviking/_build_lakebase/_build_jiuwen_provider（49-58），rail 构造异常同样返回 None（83-85）。调用方义务：本函数不检查 memory.engine，test_engine_builtin_still_builds_caller_must_gate 断言 engine=builtin 且 provider=mem0 时仍建成 rail，引擎门控须由调用方另行完成。

来源：[jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L37–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_builder.py#L37-L47), [jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L49–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_builder.py#L49-L58), [jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L82–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_builder.py#L82-L85), [tests/unit_tests/agentserver/memory/test_external_memory_builder.py:L285–L290](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/memory/test_external_memory_builder.py#L285-L290)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":47,"path":"jiuwenswarm/agents/harness/common/memory/external_memory_builder.py","sha256":"20c723ae6df33604160a5e7f4d79f64165164360e8578a5cbd27ccd72673d9e1","start":37},{"end":58,"path":"jiuwenswarm/agents/harness/common/memory/external_memory_builder.py","sha256":"c7b9e5f9f8325444d27d933ff88151cc1f4a9b52ceaa96252caf1c32d482c050","start":49},{"end":85,"path":"jiuwenswarm/agents/harness/common/memory/external_memory_builder.py","sha256":"6f43545c6bb856b2497c1ed10c39ac15df59834e102d5330068aa88496f7a0bc","start":82},{"end":290,"path":"tests/unit_tests/agentserver/memory/test_external_memory_builder.py","sha256":"0961573905109dca7d88201c39d935e8467738bb8ae690d8ec4c0e45f7081cf6","start":285}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=memory facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=73fd7f78b73bd11a7986be99704e63aee95c3c4a9c1b73bf8d761bac4b34b6a8 -->
**外接记忆配置与构造的单元测试入口**
入口一：tests/unit_tests/agentserver/memory/test_external_memory_config.py::test_engine_gates_truth_table（117-126）参数化 memory.engine 取 builtin/external/both/none，断言 is_builtin_memory_allowed 与 is_external_memory_allowed 的真值表（builtin→仅内置，none→双双为假）。入口二：test_external_memory_builder.py::test_provider_raises_returns_none（519-524）令 provider __init__ 抛 RuntimeError，断言 build_external_memory_rail 返回 None，覆盖构造失败的降级分支。所提供测试切片集中于 external 配置与 builder，此处仅陈述断言，不声称测试现已运行通过。

来源：[tests/unit_tests/agentserver/memory/test_external_memory_config.py:L117–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/memory/test_external_memory_config.py#L117-L126), [tests/unit_tests/agentserver/memory/test_external_memory_builder.py:L519–L524](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/memory/test_external_memory_builder.py#L519-L524)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":126,"path":"tests/unit_tests/agentserver/memory/test_external_memory_config.py","sha256":"e03bb3f7fed4ff4fc4acb21c68e79e7b371835ce78f06ddc9be2b2d9c00ef4d4","start":117},{"end":524,"path":"tests/unit_tests/agentserver/memory/test_external_memory_builder.py","sha256":"790ec8bdccdcba2b944262dacd931a67660c858c9a15ddaeddbdfdcfa0e5574f","start":519}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=memory facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=65994b96fe48d1c9ed104d985339e903053eb46c1e8029e84cc87b5b8a4b261d -->
**run_sweep：executor 扫描，扫描异常或结果为空即 return；仅 succeeded_ids 非空时写 scanned_sessions checkpoint**
run_sweep 经 run_in_executor 执行 scan_new_sessions：该阶段抛异常记 '[Sweeper] Scan stage failed' 后 return，sessions 为空也 return。逐 session 抽取成功时给 items 标 source_session_id 并计入 succeeded_ids，异常计入 failed_ids；仅当 succeeded_ids 非空才把 history_mtime 与 round_count 写入 scanned_sessions。

来源：[jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py:L133–L155](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py#L133-L155), [jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py:L160–L179](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py#L160-L179), [jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py:L206–L219](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py#L206-L219)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":155,"path":"jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py","sha256":"76d7a03446887805ad41b96bbc6eaecebe912ecefa9caa117f018db2e4dc41f1","start":133},{"end":179,"path":"jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py","sha256":"76eae401822535d8ba18485e2b63bcf83abea7528e8d688aadaf0d4ad08618d0","start":160},{"end":219,"path":"jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py","sha256":"586ac437c335450200c9f1216457af639dee12257ee8cbd4a66ccd47f9bb4672","start":206}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=memory facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d90e7efdc7989c358e3abaf31aa5f18ad7241f6ddf6c7b96e49341e172d7f423 -->
**build_external_memory_rail 依赖 openjiuwen 的 ExternalMemoryRail 可导入；导入异常或 provider 为空时返回 None**
该工厂先 `from openjiuwen.harness.rails import ExternalMemoryRail`，导入抛任意异常仅 logger.warning '[ExternalMemoryBuilder] ExternalMemoryRail import failed' 后返回 None；随后 ext_cfg 的 provider 为空同样返回 None，rail 静默不构建。

来源：[jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L30–L49](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/external_memory_builder.py#L30-L49)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":49,"path":"jiuwenswarm/agents/harness/common/memory/external_memory_builder.py","sha256":"b13ab8771ed14d7326448305a9b5b3d02f2ec8a1c9af1cedbc16a1baee364a5f","start":30}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=memory facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dcf652471f78c35fb3965400109de676a32472a35c9f8e190ad3eaf8632bf1a2 -->
**_search_vector 仅 SQL try 块内异常降级到 _search_vector_fallback；前置 embed_query/建表在 try 之外，异常向上传播**
触发：try 块内（chunks/vec0 SQL）任意异常；守护分支 logger.debug 'Vector search with sqlite-vec failed' 后返回 _search_vector_fallback(query_vec, limit) 的结果。embed_query/_ensure_vector_table 位于 try 之前，异常不降级、向上传播；fallback 中 query_norm<1e-10 返回 []。

来源：[jiuwenswarm/agents/harness/common/memory/manager.py:L878–L889](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/manager.py#L878-L889), [jiuwenswarm/agents/harness/common/memory/manager.py:L890–L942](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/manager.py#L890-L942), [jiuwenswarm/agents/harness/common/memory/manager.py:L944–L954](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/manager.py#L944-L954)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":889,"path":"jiuwenswarm/agents/harness/common/memory/manager.py","sha256":"d056f4421057cd1a7688349c75fcb90482adb7b7f37b72fd074cb6c3a703bd63","start":878},{"end":942,"path":"jiuwenswarm/agents/harness/common/memory/manager.py","sha256":"99cf01a9d3e6c1ed584a8b0887714bace21e38ed049379f3971b05f6f9c44bfe","start":890},{"end":954,"path":"jiuwenswarm/agents/harness/common/memory/manager.py","sha256":"71e7fb23ea8f4f7ef1f67cdb98b08b83493427675383e4cbae8629318504bdd8","start":944}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=memory facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6a87d2de175c95147250ef4b256b52aed1e27fa82488a5d7e0ad3c48ec575395 -->
**向量检索把 top-k 排序下推 vec0 SQL，但先全量载入通过 source_filter 的 chunks 行**
设计推断（非作者历史意图）：

收益（推断）：距离排序与 LIMIT 由 vec_distance_cosine 的 vec0 SQL 完成，top-k 在扩展内选出；代价（推断）：先用 chunks SELECT 把通过 source_filter 的全部行（含截断 snippet）载入 chunk_map，成本随命中 chunk 数而非 limit 增长。

来源：[jiuwenswarm/agents/harness/common/memory/manager.py:L895–L925](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/memory/manager.py#L895-L925)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":925,"path":"jiuwenswarm/agents/harness/common/memory/manager.py","sha256":"056d7bb1dd793f5dec3608a102c2ae6ec726dffb40821553e3a3979c712215d9","start":895}],"trace":[]} -->
<!-- /kb:depth -->
