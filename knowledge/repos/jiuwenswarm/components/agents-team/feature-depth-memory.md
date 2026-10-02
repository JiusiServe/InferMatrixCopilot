---
title: "长期记忆：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/config.py:L250-L281, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/config.py:L207-L247, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/dreaming/sweeper.py:L51-L71, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L37-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L49-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/memory/external_memory_builder.py:L82-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/memory/test_external_memory_builder.py:L285-L290, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/memory/test_external_memory_config.py:L117-L126, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/memory/test_external_memory_builder.py:L519-L524]
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
