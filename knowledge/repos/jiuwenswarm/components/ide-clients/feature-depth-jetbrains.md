---
title: "JetBrains 客户端：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L21-L26, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L39-L42, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/ide/jetbrains/JetBrains插件.md:L20-L25", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L52-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L31-L62, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/SessionManager.kt:L159-L179, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/ide/jetbrains/JetBrains插件.md:L15-L25", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L43-L49, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/WsClient.kt:L82-L89, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/ide/jetbrains/JetBrains插件.md:L147-L147"]
feature: "jetbrains"
entry_points: ["jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt"]
source_globs: ["jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt", "jiuwenswarm/channels/ide/packages/jetbrains-plugin/*"]
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

<!-- kb:depth feature=jetbrains facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1377cad77af096a9b66fcb55c488440f215126f1837f0c5903382a0b75b4bd70 -->
**CONNECTED 后 15 秒仍处于连接且无会话 ID 才重连一次**
状态监听器在 WsStatus.CONNECTED 时调用 scheduleAckRetry：仅当 ackRetryPending 为假才置真并调度 15 秒任务，任务先复位标志，再在 ws.isConnected() 且 session.sessionId == null 时记日志并调用 ws.reconnect()；reconnect 在未销毁时取消重试定时、retryCount 清零、以 1000 关闭旧 ws 后 connect()。

来源：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L43–L49](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L43-L49), [jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L52–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L52-L61), [jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/WsClient.kt:L82–L89](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/WsClient.kt#L82-L89)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":49,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt","sha256":"802bc1e71cd7f423dc3500d1a98d3079eda78ce5674a73dce658e437a79c0dcc","start":43},{"end":61,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt","sha256":"9ce01a65eba7d0c8e8fe27305b4fddf0e006cc679b75b2d9b9472ebf93862489","start":52},{"end":89,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/WsClient.kt","sha256":"007da34722c6007a512a55ace2b40091ea658a0c8c90fc1ba54ae509be84ca2b","start":82}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=jetbrains facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4c63ec38fab07b50e0b7b99ae591481e12b956c4a86978d5f1f5818840830c44 -->
**sendChat：无会话时返回 false；所示行构造 chat.send 请求至 params.content**
sendChat(content, mode, requestId, ideContext=null, mediaItems=null, model=null): Boolean——sessionId 为 null 时直接返回 false，调用方须先建立会话；ideContext 非空白时拼为 content 加空行再加 ideContext；所示行构造 id=requestId、type="req"、channel_id=channelId、method="chat.send" 的消息，内容止于 params 的 content 字段。

来源：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/SessionManager.kt:L159–L179](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/SessionManager.kt#L159-L179)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":179,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/client/SessionManager.kt","sha256":"029966aedc50bc22208a18fe105d403fe9abaf6a05dd979128560d2b40053d16","start":159}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=jetbrains facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=76a261f82f9d3620e9f09a5f841c149cfe65c812fcd87f2a04a825b5f4da55f7 -->
**服务构造读取 JiuwenSwarmSettings：保活开关决定传入间隔，autoConnect 决定首连**
JiuwenSwarmService 构造时以 settings.wsUrl 创建 WsClient，仅当 keepAliveEnabled 为真才传入 keepAliveInterval，否则传 0；settings.channelId 传入 SessionManager；init 仅当 settings.autoConnect 为真才调用 ws.connect()。文档记录默认值：启动时连接=开，保活 ping 间隔 30 秒（5–300）。

来源：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L21–L26](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L21-L26), [jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L39–L42](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L39-L42), [docs/zh/ide/jetbrains/JetBrains插件.md:L15–L25](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/jetbrains/JetBrains%E6%8F%92%E4%BB%B6.md#L15-L25)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":26,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt","sha256":"57dc5030ba3b9418dc00b34cd667ba8c1a3f11fc66044cd86ede943324c93566","start":21},{"end":42,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt","sha256":"db86cbf61eb9080cc7d8003b50dacc76f7fd41765c8f7dfbc68fd7d7fa6da202","start":39},{"end":25,"path":"docs/zh/ide/jetbrains/JetBrains插件.md","sha256":"49ad046862f87a4eb1d61aa69c640f30c4e1908827005f45fa647a1f0ea9fa1b","start":15}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=jetbrains facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bc41b3fd86958ce24f49539bffc4d9bec0cfdf216ef35fc24009197dcf4b1c2c -->
**缺少 connection.ack 时的一次性 15 秒重连（去重且断开重置）**
触发：服务器未就绪时连接后跳过 connection.ack。防护分支：CONNECTED 进入 scheduleAckRetry，ackRetryPending 去重；15 秒后仅当 ws.isConnected() 且 session.sessionId==null 才记日志并 ws.reconnect() 一次；DISCONNECTED/RECONNECTING 把 ackRetryPending 置回 false。

来源：[jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt:L31–L62](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt#L31-L62)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":62,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt","sha256":"d7433e47f906806e9b403608cfabe31236d9840ac1e697c8e842dd017e6b3642","start":31}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=jetbrains facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=55850dc513d3f3f6348a70e718345c3ecc9a6de20c547f72d88a502ab137934f -->
**Swarm Map 调试日志默认关闭的文档化手动观察步骤（未执行）**
文档中的人工验收步骤（本轮未执行）：

文档记载 Swarm Map 的 ☰ 菜单 → 调试日志 默认关闭；手动开启后预期实时显示团队事件与工具归属日志，并带清除/复制。此为现有文档化手动步骤，本次未执行（NOT EXECUTED）。

来源：[docs/zh/ide/jetbrains/JetBrains插件.md:L147–L147](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/jetbrains/JetBrains%E6%8F%92%E4%BB%B6.md#L147-L147)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":147,"path":"docs/zh/ide/jetbrains/JetBrains插件.md","sha256":"d05c5ba10fbe39de91d6e3393c752b4c6c449863bc2194d78a258886306a6d50","start":147}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
