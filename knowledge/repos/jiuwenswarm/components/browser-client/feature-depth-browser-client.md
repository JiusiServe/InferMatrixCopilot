---
title: "Chromium 浏览器扩展：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/background/index.ts:L211-L249, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/background/index.ts:L236-L248, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/background/ContextCache.ts:L1-L12, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/browser-extension/浏览器扩展.md:L25-L36", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/background/SessionManager.ts:L90-L93, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts:L149-L153, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/background/index.ts:L60-L64, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts:L174-L179, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/background/SessionManager.ts:L161-L170, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/background/index.ts:L117-L135, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/background/index.ts:L202-L249, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/tests/ContextCache.test.ts:L17-L25, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/tests/ContextCache.test.ts:L45-L51, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/browser/frontend/src/background/index.ts:L230-L236]
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

<!-- kb:depth feature=browser-client facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f4dca54d9549b798041753fc8c143c074bf40590089324961c1bbad8992f52b7 -->
**handleSendAgent：无活动会话时向来源端口回发错误并 return，否则聚合上下文后经 client.send 发送**
端口 onMessage 回调将未类型化 JSON 转型后交给 handleSidePanelMsg，按 sidePanelHandlers 查表分发。handleSendAgent 以 msg.action 为守卫；activeSessionId 为空时向该 port 回发 {type:"error"} 并局部 return；否则把 cache.aggregate(tabIds, MAX_CONTEXT_CHARS) 得到的 context（非空时与 message 以 --- 拼接为 fullContent）作为 content/query，经 client.send(GW_METHOD.CHAT_SEND, {content, query, session_id}) 发送。

来源：[jiuwenswarm/channels/browser/frontend/src/background/index.ts:L117–L135](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/index.ts#L117-L135), [jiuwenswarm/channels/browser/frontend/src/background/index.ts:L202–L249](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/index.ts#L202-L249)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":135,"path":"jiuwenswarm/channels/browser/frontend/src/background/index.ts","sha256":"df833c5b994da3128f22b997d29bd05f1e8700c89fdd2e266597db000aa23c29","start":117},{"end":249,"path":"jiuwenswarm/channels/browser/frontend/src/background/index.ts","sha256":"820028db8e1454e2928400f7047304eafafd4c4264c0b5b091a5f0853687c229","start":202}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=browser-client facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6fb550c5ffbd748ddb9b6678e63dfab5f744dcb3e3edd70a61ab6021434c0ba0 -->
**设置页可配置项与代码内缺省（文档未示具体默认值）**
文档声明设置页可配置服务器主机、端口、默认会话模式与行为开关，但未给出具体默认值。代码内可见缺省/优先级：会话行 mode 为 (ss.mode) || "chat"；handleBgMsg 归一键为 action ?? type ?? ""，action 优先，使同一 switch 兼容后台回复与服务器原始信封。

来源：[docs/zh/browser-extension/浏览器扩展.md:L25–L36](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/browser-extension/%E6%B5%8F%E8%A7%88%E5%99%A8%E6%89%A9%E5%B1%95.md#L25-L36), [jiuwenswarm/channels/browser/frontend/src/background/SessionManager.ts:L90–L93](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/SessionManager.ts#L90-L93), [jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts:L149–L153](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts#L149-L153)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":36,"path":"docs/zh/browser-extension/浏览器扩展.md","sha256":"d6809fa69a0d7399f5d745d6880719b025d437af8cc7106cd97eb77a7581d7d9","start":25},{"end":93,"path":"jiuwenswarm/channels/browser/frontend/src/background/SessionManager.ts","sha256":"a1953e8252755dec133044188d64ed2b23fd7ab55e7bf94232907db3c64471c3","start":90},{"end":153,"path":"jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts","sha256":"dd021a87a7b067b3c0b62e1f881856a386d9a9a3066148ce8d8d79af5a5f28e1","start":149}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=browser-client facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b2d6d9cc4fd9195c352f5724eaabb880ac7978caef7d2aa2c088488a4f714973 -->
**后台-侧栏端口耦合与 ContextCache/tabWatcher 上下文依赖**
sessionMgr.onChange 与服务器流信封都经 broadcastToSidePanel 下发，侧栏因此以 action ?? type 双键分发（注释明言两类消息键不同）。发送路径耦合 ContextCache.aggregate、tabWatcher.extractFromTab 与固定页存储，页面上下文须折叠进 content 才被网关使用。

来源：[jiuwenswarm/channels/browser/frontend/src/background/index.ts:L60–L64](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/index.ts#L60-L64), [jiuwenswarm/channels/browser/frontend/src/background/index.ts:L211–L249](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/index.ts#L211-L249), [jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts:L149–L153](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts#L149-L153)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":64,"path":"jiuwenswarm/channels/browser/frontend/src/background/index.ts","sha256":"2fd6216bc3c8b1140f4e031a9577ffabce59323c3409efb1cd1b7b5ba36315f8","start":60},{"end":249,"path":"jiuwenswarm/channels/browser/frontend/src/background/index.ts","sha256":"7fd9debe559cefc82a2e7bc3bf19cd46c2ddc4addbc55aadd45e1633ef258c20","start":211},{"end":153,"path":"jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts","sha256":"dd021a87a7b067b3c0b62e1f881856a386d9a9a3066148ce8d8d79af5a5f28e1","start":149}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=browser-client facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9dd1112547b52ad63dc71dfdbb9508d69077a132906b099682fff41012da4268 -->
**无活动会话与错误信封的守卫分支及传播**
触发 !sessionMgr.activeSessionId：handleSendAgent 不发网关请求，向来源 port 回 {type:"error",payload:{message:"No active session"}}；侧栏 error 分支 endTurn() 后渲染 humanizeError（消息缺省 "Unknown error"）。setActiveSession 遇未知 id 仅 log.warn 返回，不切换。

来源：[jiuwenswarm/channels/browser/frontend/src/background/index.ts:L211–L249](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/index.ts#L211-L249), [jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts:L174–L179](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts#L174-L179), [jiuwenswarm/channels/browser/frontend/src/background/SessionManager.ts:L161–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/SessionManager.ts#L161-L170)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":249,"path":"jiuwenswarm/channels/browser/frontend/src/background/index.ts","sha256":"7fd9debe559cefc82a2e7bc3bf19cd46c2ddc4addbc55aadd45e1633ef258c20","start":211},{"end":179,"path":"jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts","sha256":"6397929c56c528bfd176d0f19affffd8694e128d9c088f55f5951c7dcdaa535f","start":174},{"end":170,"path":"jiuwenswarm/channels/browser/frontend/src/background/SessionManager.ts","sha256":"f233afb45f47fc1672e0e5bab86221ab1e65f92d3a2e88cce66843aa58bed973","start":161}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=browser-client facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8c568b39b27de0c419ed34f138a49dd472de7008bcc367ae84c3379895341e4b -->
**ContextCache 所示用例直接断言 helper 的存取与截断（helper_unit）**
ContextCache.test.ts 直接 new ContextCache()：L17–L25 断言 set/get/delete 往返，L45–L51 断言 aggregate 在超过 maxChars 时输出含 "truncated"；这些断言仅作用于该 helper 的方法，而 handleSendAgent 在 L233/L236 使用 cache.set 与 cache.aggregate。

来源：[jiuwenswarm/channels/browser/frontend/tests/ContextCache.test.ts:L17–L25](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/tests/ContextCache.test.ts#L17-L25), [jiuwenswarm/channels/browser/frontend/tests/ContextCache.test.ts:L45–L51](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/tests/ContextCache.test.ts#L45-L51), [jiuwenswarm/channels/browser/frontend/src/background/index.ts:L230–L236](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/index.ts#L230-L236)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":25,"path":"jiuwenswarm/channels/browser/frontend/tests/ContextCache.test.ts","sha256":"dbdb7e3ee01159709bba24ba389576654504ed8e32970ea45a97c7172359b65e","start":17},{"end":51,"path":"jiuwenswarm/channels/browser/frontend/tests/ContextCache.test.ts","sha256":"9cb38546e608ad35afcd6b2272448fbad3ebf73f299fb8de9f806c00ca94cb3e","start":45},{"end":236,"path":"jiuwenswarm/channels/browser/frontend/src/background/index.ts","sha256":"d1d8c5ceeb07c11933f90ea9a4347f21be8c8f10e563ae4d1bf0a52f5d77af1e","start":230}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
