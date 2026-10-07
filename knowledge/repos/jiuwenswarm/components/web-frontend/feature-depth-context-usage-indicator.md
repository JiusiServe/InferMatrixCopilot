---
title: "上下文占用指示器（环形/悬浮提示/明细弹层）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L62-L78, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L142-L158, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L64-L78, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L142-L148, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L18674-L18701, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L233-L238, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface.py:L5084-L5096, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/utils/stream_utils.py:L128-L140, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/contextUsageDom.test.mjs:L1-L17, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/contextUsageDom.test.mjs:L32-L80, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/contextUsageDom.test.mjs:L139-L195]
feature: "context-usage-indicator"
entry_points: ["jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.css", "jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.css", "jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx", "jiuwenswarm/server/runtime/agent_adapter/interface_deep.py", "jiuwenswarm/server/utils/stream_utils.py"]
---

# 上下文占用指示器（环形/悬浮提示/明细弹层）：实现深读

[功能概览](feature-context-usage-indicator.md) · [owner 入口](_index.md)

<!-- kb:depth feature=context-usage-indicator facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dcd5b936b94c888113b0f25f3cdef87ed3485bbc7d6f0b4f44b1843e8dea4aba -->
**渲染前按 mode/会话/快照守卫，null 字段降级为“未上报”**
组件从 useSessionStore 按 activeSessionId 读取 mode 与 contextUsageSnapshot；当 mode 不是 'agent' 或 'team'、无 activeSessionId 或无 snapshot 时直接 return null（L142）。否则解构 snapshot.context_window，occupancy_rate/input_tokens/limit_tokens 为 null 时显示 t('chat.contextUsage.notReported')，ringPercent 仅在 rate 非 null 时计算（L144–L151）。

来源：[jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L62–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L62-L78), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L142–L158](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L142-L158)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":78,"path":"jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx","sha256":"a16ff8043543bc4953264fa7a78a6814ee9c2e58cb30a2dc5459f5643ae9e344","start":62},{"end":158,"path":"jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx","sha256":"333d1b4b473c5f24ddb73d9ddbb9392af5e0022a35a055418bf35c8ef404fb9a","start":142}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=context-usage-indicator facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3fa32fd0423b067f5da6d37090866a294c1c503d0055054e10fd8fa9b30e1f03 -->
**get_context_usage(session_id) 异步返回上下文占用统计字典**
JiuWenSwarm.get_context_usage 是 async 方法，入参 session_id（会话ID），返回包含上下文窗口总量与当前占用量、系统提示词/对话消息/工具定义各自 token 消耗及占用百分比的字典；具体统计字段由实现填充，所示行仅为文档字符串。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface.py:L5084–L5096](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface.py#L5084-L5096)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":5096,"path":"jiuwenswarm/server/runtime/agent_adapter/interface.py","sha256":"9664b1612d7f68bb52ed10484c682cccc35d6d055194be3c74543103cf2466d5","start":5084}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=context-usage-indicator facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a603caf989d9071e4b8e11328fbb3cc0cc255048e19a9f1793421b8bd20d134f -->
**mode 缺省回退 'agent'，snapshot 缺省 null（runtimes 查找按会话）**
组件用 `state.runtimes[activeSessionId ?? '']?.mode ?? 'agent'` 读取模式，无会话运行时时按 'agent' 处理；`contextUsageSnapshot ?? null` 缺省为 null，而 null snapshot 使组件整体不渲染（L65–L66 与 L142 守卫）。

来源：[jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L64–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L64-L78), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L142–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L142-L148)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":78,"path":"jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx","sha256":"d6bd03141937ac54237d83e98329c8d44e620f9d6336237bbc77ba157bc2482c","start":64},{"end":148,"path":"jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx","sha256":"0df00e0b4a8dd8ced361e97d790388caec8808244c5ad8808f88c7cb4af8b2b5","start":142}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=context-usage-indicator facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=120ac86cca3fc9a5904b599ae25ff25b8d44b5b591df171129f04fc8418e1cab -->
**快照构建抛异常时记 warning 并返回 None，不影响 /compact**
get_context_usage_event 的 try 块包裹 build_snapshot，except Exception 时 logger.warning("manual context usage snapshot failed", exc_info=True) 并返回 None，注释明确 usage telemetry 不得使 /compact 失败；build_snapshot 不可调用时同样返回 None（debug 日志）。前端悬浮层对 displayCacheRate 为 null 时跳过缓存命中率行。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L18674–L18701](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py#L18674-L18701), [jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx:L233–L238](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L233-L238)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":18701,"path":"jiuwenswarm/server/runtime/agent_adapter/interface_deep.py","sha256":"d603f95dfd6f1f2b435de1cb5e00bfceaa5743835b343a3d5e0002853c53590e","start":18674},{"end":238,"path":"jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx","sha256":"9777f1a1cdcebb16b0b0c37009d932ae93e41dc0284925e2f6045b2ae1e24598","start":233}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=context-usage-indicator facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8dd501ffe1be729f19ace4dab40a4c8e50b64d296393f6e68ab2eb8db7e4784f -->
**服务端回填旧版 Core 载荷以保持前端协议版本容错**
设计推断（非作者历史意图）：

stream_utils 在 usage_payload 顶层缺少 session_kv_cache_hit_rate 时，若嵌套 kv_cache.session 是 dict 则回填其 weighted_hit_rate，注释明示目的是让前端协议版本容错；收益是旧载荷仍可展示，代价是服务端需维护兼容分支。此为推断标注：收益/代价由注释与实现推断。

来源：[jiuwenswarm/server/utils/stream_utils.py:L128–L140](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/utils/stream_utils.py#L128-L140)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":140,"path":"jiuwenswarm/server/utils/stream_utils.py","sha256":"b296e7814904217f00fbea5771d0d220152bcd3e59b512a22238fd2f40fd7be8","start":128}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=context-usage-indicator facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a32ed66ef9a926b1aeaee5e930f8467e9f01178e32f78e84b46910c233a07b8b -->
**contextUsageDom.test.mjs 挂载真实组件并断言 tooltip/明细 DOM 更新**
测试 contextUsageDom.test.mjs 通过 receiveContextUsage 注入快照后，断言 trigger aria-label 含 50%、tooltip 文案含 50%/88.3% 且不含其他来源数值、明细含 4 个类别与 4 个分段、后续快照更新 metric 为 120% 与分段宽度 12.3%，并验证 Escape 关闭且焦点还原、关闭按钮与外点 pointerdown 关闭。这是已有的自动化运行时测试，此处仅描述未执行。

来源：[jiuwenswarm/channels/web/frontend/tests/contextUsageDom.test.mjs:L1–L17](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/contextUsageDom.test.mjs#L1-L17), [jiuwenswarm/channels/web/frontend/tests/contextUsageDom.test.mjs:L32–L80](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/contextUsageDom.test.mjs#L32-L80), [jiuwenswarm/channels/web/frontend/tests/contextUsageDom.test.mjs:L139–L195](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/contextUsageDom.test.mjs#L139-L195)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":17,"path":"jiuwenswarm/channels/web/frontend/tests/contextUsageDom.test.mjs","sha256":"d27c11f7878f3278faaad075da3ab913b5a24a2ff6592e1444dad7115f7220ae","start":1},{"end":80,"path":"jiuwenswarm/channels/web/frontend/tests/contextUsageDom.test.mjs","sha256":"6a78d70fb25b0256474e2b4c181fc286d79aefca4d0e3ed2879d06536efb8cb4","start":32},{"end":195,"path":"jiuwenswarm/channels/web/frontend/tests/contextUsageDom.test.mjs","sha256":"6eb88b93b0e3ba98aa521fa00307a829ea8ff5df42078d837efbcc8fb77d77ca","start":139}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
