---
title: "VS Code 客户端：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/extension.ts:L21-L39, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts:L145-L152, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/ide/vscode/VSCode插件.md:L23-L23", "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/ide/vscode/VSCode插件.md:L109-L112", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts:L63-L103, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/client/SessionManager.ts:L161-L170, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts:L102-L106, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts:L953-L966, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts:L23-L31]
feature: "vscode"
entry_points: ["jiuwenswarm/channels/ide/packages/vscode-extension/src/extension.ts"]
source_globs: ["jiuwenswarm/channels/ide/packages/vscode-extension/src/extension.ts", "jiuwenswarm/channels/ide/packages/vscode-extension/*"]
---

# VS Code 客户端：实现深读

[功能概览](feature-vscode.md) · [owner 入口](_index.md)

<!-- kb:depth feature=vscode facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b5e939b8d4b51ac3b78c641f5e57956baf3b09615dec0592b88ba4ed601ca50e -->
**host 决定 ws/wss 及默认值**
jiuwenswarm.host 默认 '127.0.0.1'、port 默认 19000、channelId 默认 'ide'、autoConnect 默认 true；host 为空/127.0.0.1/localhost/::1 时用 ws，其余值用 wss。keepAlive.enabled 默认 true、interval 默认 30（秒），enabled 为 false 时 pingIntervalMs 传 0、startPing 直接跳过心跳。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/extension.ts:L21–L39](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/extension.ts#L21-L39), [jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts:L145–L152](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts#L145-L152)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/extension.ts","start":21,"end":39,"sha256":"7dbf0613dd807298d8c0fc91dcaed3f3a5f9fd2300426883a824f73c580472fd"},{"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts","start":145,"end":152,"sha256":"d54bc92d0bccfc58b871aa0da6cfba59dbe09f5b197b7f5767102ab8f7ba6418"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=vscode facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dc5c50d9014bdbe5a3bb52c10bdfcb17dd897d28426b3d23fc7039c8d28ebd80 -->
**ChatPanel.show()：面板已存在则 reveal 并刷新后返回，否则创建 webview、接线并启动轮询**
panel 已存在时 reveal(Beside) 后 sendCurrentStatus()+refreshMetrics() 即返回；否则创建 'JiuwenSwarm' webview（enableScripts、retainContextWhenHidden），html 取自 getHtml，注册 onDidReceiveMessage→handleWebviewMessage 与 onDidDispose（停内存轮询、清 disposables 与 pending、panel=undefined）；末尾仅 ws.isConnected() 时 sendCurrentStatus()，随后 refreshMetrics()+startMemoryPolling()。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts:L63–L103](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts#L63-L103)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":103,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts","sha256":"ab8e6dc98fd5f9c4781bbe1a6a99aa5e16ec59c73f6c0d50bf52ea565126261d","start":63}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=vscode facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=57d192dfe5e69e82d0ea2a492e17b337bf79d4229ab276802f5a70ae9d40fbcf -->
**SessionManager.loadHistory(sid, pageIdx=1)：返回 ws.send 布尔值，历史数据不随返回值给出**
构造 'history.get' 请求（带 this.channelId）并 `return this.ws.send(msg)`：socket readyState 非 OPEN 时返回 false；按所示注释，历史以 history.message 事件流至所有 message 监听者、history.done 标记页尾——调用方须从事件消费而非等待返回值。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/client/SessionManager.ts:L161–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/client/SessionManager.ts#L161-L170), [jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts:L102–L106](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts#L102-L106)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":170,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/client/SessionManager.ts","sha256":"7953c63d9e0cfaa9cb3b03047c24fce488fb6e9d1739eec2e4425185fe0738e1","start":161},{"end":106,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts","sha256":"dd67e644ffa7838ba516b643d285559491ba90faa8c9c789d60e9e43f40bd8e7","start":102}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=vscode facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f7dc62ec37aaa589182cc04d5d19977652ccb43b1e8a27341b4b458e8f734e1 -->
**sendGitStatus 对 git 失败静默吞并；branch 为空或 'HEAD' 直接 return**
sendGitStatus() 内两条 execSync（git rev-parse --abbrev-ref HEAD 与 git status --porcelain，各配置 timeout: 3000）任一抛出即被 catch 静默吞掉（注释：非 git 仓库或 git 不可用），不 postToWebview git_status；branch 为空或等于 'HEAD'（detached）时也直接 return 不发送。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts:L953–L966](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts#L953-L966)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":966,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts","sha256":"ef358e399efa1f13b9da5dda57aaaa75eb0c89e4eefe27594374858f17cbfb01","start":953}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=vscode facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ea3c9786332ec2cfe56958b8208b6a2eb0781742f4e73a65cce20e07139ba4b6 -->
**构造时无条件把 localhost 改写为 127.0.0.1：IPv4 兼容换 IPv6 不可达（代价为推断）**
设计推断（非作者历史意图）：

WsClient 构造函数无条件执行 url.replace('://localhost:', '://127.0.0.1:')。收益（源码注释）：避免 macOS Node 17+ 先把 localhost 解析为 ::1、对仅监听 IPv4 的服务器立即连接失败。代价（推断）：仅监听 IPv6 的 localhost 服务端会被改写而无法连接。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts:L23–L31](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts#L23-L31)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":31,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts","sha256":"85284cad471047a2204a31ef66bb42422108a2d4a4162431e09ee4fc84c3f300","start":23}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=vscode facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e0dff4a395564143e8e514f2427034154b1f5c3350b2ef847054e61d51938049 -->
**文档化手动步骤：开启 loadHistoryOnSwitch 切换会话后历史自动流式加载（本轮未执行）**
文档中的人工验收步骤（本轮未执行）：

现有文档记录的操作与预期结果：保持 `jiuwenswarm.loadHistoryOnSwitch` 开启（文档默认 true），点击 ⚙ → 会话 切换到已有会话，预期历史消息自动流式加载。该手动步骤本轮未执行，仅为文档记载。

来源：[docs/zh/ide/vscode/VSCode插件.md:L23–L23](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/vscode/VSCode%E6%8F%92%E4%BB%B6.md#L23-L23), [docs/zh/ide/vscode/VSCode插件.md:L109–L112](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/vscode/VSCode%E6%8F%92%E4%BB%B6.md#L109-L112)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":23,"path":"docs/zh/ide/vscode/VSCode插件.md","sha256":"d743a024bd32e81c03268e91965cee3c837206484ffb2f16037ab74ebb188019","start":23},{"end":112,"path":"docs/zh/ide/vscode/VSCode插件.md","sha256":"6843fb23444095a22cb22a6c38f2ecf7e4af7fd24956d5f39f0206bdc09dd5a8","start":109}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
