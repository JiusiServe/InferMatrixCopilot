---
title: "JetBrains 客户端：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L21-L26, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L39-L42, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/ide/jetbrains/JetBrains插件.md:L20-L25", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L52-L61]
---

# JetBrains 客户端：实现深读

[功能概览](feature-jetbrains.md) · [owner 入口](_index.md)

<!-- kb:depth feature=jetbrains facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9ebea963c6dbebf9d5c06721c04e30cc01b091ce5d33122a7a899fd55ac43577 -->
**保活与自动连接设置的消费方式**
构造 WsClient 时读 settings.wsUrl，且仅当 settings.keepAliveEnabled 为真时传入 settings.keepAliveInterval（否则传 0）。文档记录保活 ping 间隔默认 30 秒（5–300）、「启动时连接」默认开；autoConnect 仅控制 init 中是否立即 ws.connect()。

来源：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L21–L26](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L21-L26), [jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L39–L42](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L39-L42), [docs/zh/ide/jetbrains/JetBrains插件.md:L20–L25](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/jetbrains/JetBrains%E6%8F%92%E4%BB%B6.md#L20-L25)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt","start":21,"end":26,"sha256":"57dc5030ba3b9418dc00b34cd667ba8c1a3f11fc66044cd86ede943324c93566"},{"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt","start":39,"end":42,"sha256":"db86cbf61eb9080cc7d8003b50dacc76f7fd41765c8f7dfbc68fd7d7fa6da202"},{"path":"docs/zh/ide/jetbrains/JetBrains插件.md","start":20,"end":25,"sha256":"af71eddd10555e3f88535917bdfea6d37a94fd87dccee52668ae149c91fb4357"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=jetbrains facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=99c533ce7c398953b378a14ca0b61bdee23c6d0b2102cacde9d6ab4c135c6e76 -->
**固定 15 秒延迟的一次性检查**
设计推断（非作者历史意图）：

推断：选择「CONNECTED 后固定等 15 秒再检查 sessionId」而非立即重连，收益是给服务器预热（注释称约 8 秒）留出缓冲、避免高频重连；代价是固定延迟不随服务器实际就绪时间调整，且标志在回调内先被清除，可能随每次重连周期重复触发调度。

来源：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L52–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L52-L61)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt","start":52,"end":61,"sha256":"9ce01a65eba7d0c8e8fe27305b4fddf0e006cc679b75b2d9b9472ebf93862489"}],"trace":[]} -->
<!-- /kb:depth -->
