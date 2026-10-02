---
title: "Chromium 浏览器扩展：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/background/index.ts:L211-L249, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/background/index.ts:L236-L248, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/background/ContextCache.ts:L1-L12]
feature: "browser-client"
entry_points: ["jiuwenswarm/channels/browser/frontend/src/background/index.ts", "jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts"]
source_globs: ["jiuwenswarm/channels/browser/frontend/src/background/index.ts", "jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts", "jiuwenswarm/channels/browser/frontend/src/*"]
---

# Chromium 浏览器扩展：实现深读

[功能概览](feature-browser-client.md) · [owner 入口](_index.md)

<!-- kb:depth feature=browser-client facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5b3879552386fb08143f002cb8cf2e1af9d536f3000473894f10ca7e9978967a -->
**SEND_AGENT 的输入/输出契约**
MSG.SEND_AGENT 请求携带 message 与可选 tabId；若无活动会话，handler 通过 port 回发 {type:"error", payload:{message:"No active session"}} 并直接返回。调用方义务是先存在活动会话，页面上下文由后台折叠进 content 字段而非独立 context 参数。

来源：[jiuwenswarm/channels/browser/frontend/src/background/index.ts:L211–L249](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/index.ts#L211-L249)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/browser/frontend/src/background/index.ts","start":211,"end":249,"sha256":"7fd9debe559cefc82a2e7bc3bf19cd46c2ddc4addbc55aadd45e1633ef258c20"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=browser-client facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ddcfa97454d3240632d998a4be01ed9a646562a8493f4a4ae5b4b08680a6004c -->
**上下文折叠进 content 与易失缓存**
设计推断（非作者历史意图）：

网关只用 content/query 构建提示、独立 context 参数会被忽略，因此扩展把页面上下文直接拼进 content（推理：这是为兼容网关协议而做的客户端折衷，代价是用户消息与机器提取文本混在同一字段）。ContextCache 刻意做成内存易失缓存以适应服务挂起，持久性交给 storage.ts 的固定页面。

来源：[jiuwenswarm/channels/browser/frontend/src/background/index.ts:L236–L248](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/index.ts#L236-L248), [jiuwenswarm/channels/browser/frontend/src/background/ContextCache.ts:L1–L12](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/ContextCache.ts#L1-L12)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/browser/frontend/src/background/index.ts","start":236,"end":248,"sha256":"9f447168169c19b7da72cf642346f1eeaa6b583e05a98924594eacc7ac8f00b2"},{"path":"jiuwenswarm/channels/browser/frontend/src/background/ContextCache.ts","start":1,"end":12,"sha256":"579e14b7f9bcd5e5f43c69bdad53943715755362fa8dd815868f151b7134be93"}],"trace":[]} -->
<!-- /kb:depth -->
