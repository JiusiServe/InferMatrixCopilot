---
title: "声明式 root Agent 定义执行（invoke_agent/stream_agent）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/agent_definition.py:L159-L174, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/agent_definition.py:L117-L122, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/agent_definition.py:L161-L166, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/agent_definition.py:L288-L301, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/agent_definition.py:L304-L316, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/runtime/test_agent_definition.py:L41-L50, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/agent_definition.py:L265-L274, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/agent_definition.py:L319-L326, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/agent_definition.py:L276-L286, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/agent_definition.py:L252-L262, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/runtime/test_agent_definition.py:L244-L253, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/runtime/test_agent_definition.py:L277-L285, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/runtime/service.py:L1281-L1308]
feature: "runtime-agent-definition-execution"
entry_points: ["jiuwenswarm/runtime/service.py"]
source_globs: ["jiuwenswarm/runtime/service.py", "jiuwenswarm/runtime/agent_definition.py"]
---

# 声明式 root Agent 定义执行（invoke_agent/stream_agent）：实现深读

[功能概览](feature-runtime-agent-definition-execution.md) · [owner 入口](_index.md)

<!-- kb:depth feature=runtime-agent-definition-execution facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=71af07543cf659d5730a7420cb0e01ed6c2b8d029d26fdaf5ce0d1437edd4dbd -->
**RuntimeAgentExecution 冻结 kw-only 数据类：fingerprint 代理 definition，to_dict 输出 JSON 兼容描述**
公开 fingerprint 属性直接返回 definition.fingerprint；to_dict 返回 {agent, agent_fingerprint, mode}，其中 mode 经 _runtime_agent_mode 再次取 value。prepare_agent_execution 接受 definition 实例或 Mapping 加仅关键字 mode，返回不可变 RuntimeAgentExecution。

来源：[jiuwenswarm/runtime/agent_definition.py:L288–L301](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/agent_definition.py#L288-L301), [jiuwenswarm/runtime/agent_definition.py:L304–L316](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/agent_definition.py#L304-L316), [tests/unit_tests/runtime/test_agent_definition.py:L41–L50](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/runtime/test_agent_definition.py#L41-L50)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":301,"path":"jiuwenswarm/runtime/agent_definition.py","sha256":"7e48ca3d7f12b8c1917dea3886914e8b61fbf13b6261f9cfa140baa562e05c66","start":288},{"end":316,"path":"jiuwenswarm/runtime/agent_definition.py","sha256":"eaadb34d3761297db5b0ffde141d5c99876799e6fb871e1ed10284a995479c03","start":304},{"end":50,"path":"tests/unit_tests/runtime/test_agent_definition.py","sha256":"8625a74b13fb3d2112a3b0b52d3ec030dffaeb94d9dbc912021ddce276614415","start":41}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=runtime-agent-definition-execution facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f60490334196764ab1da3e1030b6f3107e9a2ac17dfb3a21431fe22fdaf458c9 -->
**tools 默认 '*' 表示使用 Runtime 已配置的工具集**
RuntimeAgentDefinition 为 frozen/slots/kw_only 数据类，tools 默认值为 "*"，skills 默认空元组，max_iterations 默认 None；docstring 说明 '*' 即复用 Runtime 配置的工具集。传入 ["*"] 列表也会归一化为 "*"。

来源：[jiuwenswarm/runtime/agent_definition.py:L159–L174](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/agent_definition.py#L159-L174), [jiuwenswarm/runtime/agent_definition.py:L117–L122](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/agent_definition.py#L117-L122)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":174,"path":"jiuwenswarm/runtime/agent_definition.py","sha256":"3c979d8be4d2b8e6292b26a155dec4ce3dbaede7a4dfa121e0febfb879e630e3","start":159},{"end":122,"path":"jiuwenswarm/runtime/agent_definition.py","sha256":"477ec983b76d808bdd0a538c10a592cf5c579c729aa5e63f76887de1f1501ebc","start":117}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=runtime-agent-definition-execution facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=57c77a604bc572ca4b2d4b7f2f77576c50cdb3579cc27f0f64c290455d1942f2 -->
**agent_definition 契约模块声明为能力契约，由 AgentRuntime 翻译，自身不执行**
RuntimeAgentExecution 文档字符串说明它是 capability contract，AgentRuntime 将其翻译为既有 AgentManager 与 Agent Adapter 输入，而非第二个执行器；模块尾 __all__ 仅导出六个契约符号。

来源：[jiuwenswarm/runtime/agent_definition.py:L265–L274](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/agent_definition.py#L265-L274), [jiuwenswarm/runtime/agent_definition.py:L319–L326](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/agent_definition.py#L319-L326)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":274,"path":"jiuwenswarm/runtime/agent_definition.py","sha256":"bb0d42eda2275e7267af0d5c4d0448c65287fa25d91a42b2eb4fe160b2cfce98","start":265},{"end":326,"path":"jiuwenswarm/runtime/agent_definition.py","sha256":"67d97ea8de1456e7a590fb6df86a5b8a83b68194349ab77ebd002ce687769139","start":319}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=runtime-agent-definition-execution facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3c8f8794eef470e2ee50a0459ae2191eadf9f3b2dcc559ef9f901731b207c0f0 -->
**WORK_NORMAL/WORK_PLAN mode 触发 AGENT_DEFINITION_MODE_UNSUPPORTED（UNSUPPORTED_MODE，field=mode），非规范 mode 触发 INVALID_MODE**
__post_init__ 中 mode 解析失败抛 code=INVALID_MODE、field="mode" 的错误（"unsupported single-Agent mode"）；命中 WORK_NORMAL/WORK_PLAN 抛 code=UNSUPPORTED_MODE、field="mode"（"custom Agent definitions are not supported in work mode"）。测试断言对应 code 且 retryable is False。

来源：[jiuwenswarm/runtime/agent_definition.py:L276–L286](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/agent_definition.py#L276-L286), [jiuwenswarm/runtime/agent_definition.py:L252–L262](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/agent_definition.py#L252-L262), [tests/unit_tests/runtime/test_agent_definition.py:L244–L253](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/runtime/test_agent_definition.py#L244-L253)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":286,"path":"jiuwenswarm/runtime/agent_definition.py","sha256":"38d419cdfc418aa2d206c59de0be66fcb9b179dc5d447e7cb31025ffb6db89b6","start":276},{"end":262,"path":"jiuwenswarm/runtime/agent_definition.py","sha256":"653548cb8f13c04f1232468b6e2e5edf471cc7d8fdc417366c5b87bd0e682d3f","start":252},{"end":253,"path":"tests/unit_tests/runtime/test_agent_definition.py","sha256":"5206dd1521371cfaf87b8606442187c0a87aadf5f9577f86fce58fd600fbc3b2","start":244}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=runtime-agent-definition-execution facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a05c7e93a38fdb972c3a2ae00cebbccc08a53901cc6898f42585d08bdde5176f -->
**拒绝显式工具白名单：换取契约稳定，代价是暂时无法按 Agent 限权**
设计推断（非作者历史意图）：

实现注释写明拒绝 allowlist 是有意的，直到 Runtime 能在所有 rails 和扩展贡献完工具之后再 enforcing。推断（inference）：收益是避免承诺无法执行的权限承诺，代价是定义方当前只能用全量工具集 '*'。

来源：[jiuwenswarm/runtime/agent_definition.py:L161–L166](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/agent_definition.py#L161-L166)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":166,"path":"jiuwenswarm/runtime/agent_definition.py","sha256":"93c3b6afe235956c33e1ce13141ee6c9be62942a78a2753c3b97ff092f5009ab","start":161}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=runtime-agent-definition-execution facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7e50961d331d45c0525d7ff34f8c4725e7548495bc48892aaa6838b828b8a36a -->
**单元测试直接调用 prepare_agent_execution 断言 mode 错误码与先校验定义再校验 mode 能力**
test_work_modes_return_stable_unsupported_error 对两个 WORK mode 断言 AGENT_DEFINITION_MODE_UNSUPPORTED、field=mode、retryable False；test_prepare_accepts_mapping_and_validates_before_mode_capability 用非法 name 映射加 WORK_NORMAL 断言先得到 field=name 的 AGENT_DEFINITION_INVALID。这些是运行时断言，但仅覆盖契约校验层，未执行真实 Agent 执行。

来源：[tests/unit_tests/runtime/test_agent_definition.py:L244–L253](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/runtime/test_agent_definition.py#L244-L253), [tests/unit_tests/runtime/test_agent_definition.py:L277–L285](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/runtime/test_agent_definition.py#L277-L285)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":253,"path":"tests/unit_tests/runtime/test_agent_definition.py","sha256":"5206dd1521371cfaf87b8606442187c0a87aadf5f9577f86fce58fd600fbc3b2","start":244},{"end":285,"path":"tests/unit_tests/runtime/test_agent_definition.py","sha256":"de5b1d9f64632820653a8d159a158e755b70d467f80a1d9e38e83119016f8756","start":277}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=runtime-agent-definition-execution facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=22f7a2e2bfe27ed419801637001e5b8500fc0322e09e127d3c81230618262a23 -->
**stream_agent 入口：校验并改写定义后委托既有 stream 链**
stream_agent 先 await self.start() 并做会话归属校验；当 request.params 是 dict 时取其中的 mode 经 resolve_mode_capability 解析，再 validate_agent_definition 得到 execution，随后 _bind_agent_execution_request 改写请求并 await _claim_agent_execution_owner 绑定 owner，最后在 aclosing 中把 bound_request 连同 _agent_execution=execution 透传给 self.stream，逐个 yield 事件。

来源：[jiuwenswarm/runtime/service.py:L1281–L1308](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/runtime/service.py#L1281-L1308)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1308,"path":"jiuwenswarm/runtime/service.py","sha256":"182c537e98542da35fad4b93bbf1cc8427c1a6b21161eb2a0a73841f357d81be","start":1281}],"trace":[]} -->
<!-- /kb:depth -->
