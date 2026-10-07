---
title: "Chat Session Stats Bar and Per-Turn Mini Charts：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/shared-webview/chat.html:L3398-L3407, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/shared-webview/chat.html:L3391-L3396, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/shared-webview/chat.html:L4348-L4361, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/shared-webview/chat.html:L4352-L4364, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/ide/jetbrains/JetBrains插件指南.md:L139-L155", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/shared-webview/chat.html:L4503-L4516]
feature: "chat-session-stats-dashboard"
entry_points: ["jiuwenswarm/channels/ide/packages/shared-webview/chat.html"]
source_globs: ["jiuwenswarm/channels/ide/packages/shared-webview/chat.html"]
---

# Chat Session Stats Bar and Per-Turn Mini Charts：实现深读

[功能概览](feature-chat-session-stats-dashboard.md) · [owner 入口](_index.md)

<!-- kb:depth feature=chat-session-stats-dashboard facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ecb9fa39e7e147e1ca20fdc0d4d9de902d3fadebbdef9549c25eb69ae07bc49c -->
**renderTokenCounter callback: only when state.contextWindow > 0, derives pct and estimated used tokens**
调用 renderTokenCounter(total) 时先记录 state.lastTokenTotal；若 #token-counter 元素不存在直接返回；仅当 state.contextWindow > 0 时计算 pct=contextUsagePct()，若 ctxUsed<=0 且 pct!=null 则用 Math.round(state.contextWindow*pct/100) 估算已用 tokens。

来源：[jiuwenswarm/channels/ide/packages/shared-webview/chat.html:L3398–L3407](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/shared-webview/chat.html#L3398-L3407)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3407,"path":"jiuwenswarm/channels/ide/packages/shared-webview/chat.html","sha256":"2e67012590962e0e4995b1223457f65c8ce32640ab61d1ee154e96e54de11164","start":3398}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=chat-session-stats-dashboard facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=50cc3f1a522ba53c7b7a2da809ffe1c0148a97a0aa3234acf21ce7163c460949 -->
**updateTokenBar: no-argument DOM updater reading token/state fields, early-return when bar elements absent**
updateTokenBar() takes no arguments and reads total = state.hostMetrics.sessionTokens || state.sessionStats.totalTokens, plus state.contextWindow, state.contextUsagePercent and state.contextTokensUsed; it requires elements with ids 'token-bar-wrap' and 'token-bar-fill' and returns without side effects if either is missing (line 4361).

来源：[jiuwenswarm/channels/ide/packages/shared-webview/chat.html:L4348–L4361](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/shared-webview/chat.html#L4348-L4361)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":4361,"path":"jiuwenswarm/channels/ide/packages/shared-webview/chat.html","sha256":"27866b951b4d7cd395a42a9b4ff203afc81b30ae2dfa8cc2110c667646edab61","start":4348}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=chat-session-stats-dashboard facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6d76f9a7dd7a9a410433e20fad84602e1691b596e7c30723d5422b99c4094cc5 -->
**Usage percent precedence: state.contextUsagePercent (non-null) wins over contextTokensUsed/contextWindow ratio**
若 state.contextUsagePercent != null 则直接使用该百分比；否则当 state.contextTokensUsed > 0 且 limit(=state.contextWindow) > 0 时计算比值；两者都不满足返回 null。未展示这些 state 字段的默认值或赋值来源。

来源：[jiuwenswarm/channels/ide/packages/shared-webview/chat.html:L3391–L3396](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/shared-webview/chat.html#L3391-L3396)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3396,"path":"jiuwenswarm/channels/ide/packages/shared-webview/chat.html","sha256":"208fc7e62829a141dc344c17056e437fe2c1e93cf5e02581719d2da2fa8e13bb","start":3391}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=chat-session-stats-dashboard facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5ce4faa963a4dd20b176044518e58612ab05d755f562fdf2ba1c61cfa1cba32f -->
**Stats display depends on state.contextWindow/contextTokensUsed and a token-counter DOM element**
renderTokenCounter 依赖全局 state 的 contextWindow、contextTokensUsed、contextUsagePercent 以及 id 为 token-counter 的 DOM 元素；元素缺失时静默返回（3400–3401 行），因此宿主未渲染该元素则整段显示不生效。

来源：[jiuwenswarm/channels/ide/packages/shared-webview/chat.html:L3398–L3407](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/shared-webview/chat.html#L3398-L3407)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3407,"path":"jiuwenswarm/channels/ide/packages/shared-webview/chat.html","sha256":"2e67012590962e0e4995b1223457f65c8ce32640ab61d1ee154e96e54de11164","start":3398}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=chat-session-stats-dashboard facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1dad6a2ea6cc607f6f4f7661efb8645f39ed125d3f329366b88261e58c7ffd3a -->
**updateTokenBar: null pct branch sets width 0% and removes 'visible'; missing DOM nodes cause plain early return**
When state.contextUsagePercent is null and not (state.contextTokensUsed > 0 and state.contextWindow > 0), pct becomes null and the shown branch sets fill.style.width = '0%' and removes the 'visible' class from the wrap; separately, if either DOM element is absent the function returns before any style change.

来源：[jiuwenswarm/channels/ide/packages/shared-webview/chat.html:L4352–L4364](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/shared-webview/chat.html#L4352-L4364)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":4364,"path":"jiuwenswarm/channels/ide/packages/shared-webview/chat.html","sha256":"cb65b4c336e0928ded82327bcd04dd7a4b649960c5e439b13fc62f68baf18e6c","start":4352}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=chat-session-stats-dashboard facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c21d3368bda5c0f9922a436868e0cddb1e3158965843ca8ea42b19521afc8f82 -->
**6% 最小柱高保证零值轮可见但牺牲严格比例**
bars() 对每柱高度取 Math.max(6, Math.round(v / maxVal * 100))，且归一化分母 maxTok/maxDur 由 Math.max(...,1) 保证至少为 1；收益是数值为 0 或极小的轮次仍有 6% 高度可见，代价是低于 6% 的柱不再与数值严格成比例。

来源：[jiuwenswarm/channels/ide/packages/shared-webview/chat.html:L4503–L4516](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/shared-webview/chat.html#L4503-L4516)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":4516,"path":"jiuwenswarm/channels/ide/packages/shared-webview/chat.html","sha256":"d626c3562211f8d9a0039c6a386b4efc94162cd2cbca6752441176332e039684","start":4503}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=chat-session-stats-dashboard facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=69e972f7f52cf804f852764054f7ba800dfd710b11f749a1fbaa7404646d4c06 -->
**Documented manual check (NOT EXECUTED): stats bar appears after first turn; chart toggle and hover details after two turns**
文档中的人工验收步骤（本轮未执行）：

JetBrains 插件指南记载（未执行）：统计栏在第一轮完成后出现并显示轮数/错误/Token 等指标；两轮或更多后条形图图标切换迷你图，悬停条形可查看该轮详情。此为文档记载的手工核对步骤，非自动化断言。

来源：[docs/zh/ide/jetbrains/JetBrains插件指南.md:L139–L155](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/jetbrains/JetBrains%E6%8F%92%E4%BB%B6%E6%8C%87%E5%8D%97.md#L139-L155)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":155,"path":"docs/zh/ide/jetbrains/JetBrains插件指南.md","sha256":"f22c0031a798626c8982a218dcfbb5961d746ac0c12f44422159ff86afd2820a","start":139}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
