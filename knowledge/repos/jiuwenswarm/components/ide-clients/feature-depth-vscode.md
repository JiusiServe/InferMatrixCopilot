---
title: "VS Code 客户端：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/extension.ts:L21-L39, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts:L145-L152]
---

# VS Code 客户端：实现深读

[功能概览](feature-vscode.md) · [owner 入口](_index.md)

<!-- kb:depth feature=vscode facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b5e939b8d4b51ac3b78c641f5e57956baf3b09615dec0592b88ba4ed601ca50e -->
**host 决定 ws/wss 及默认值**
jiuwenswarm.host 默认 '127.0.0.1'、port 默认 19000、channelId 默认 'ide'、autoConnect 默认 true；host 为空/127.0.0.1/localhost/::1 时用 ws，其余值用 wss。keepAlive.enabled 默认 true、interval 默认 30（秒），enabled 为 false 时 pingIntervalMs 传 0、startPing 直接跳过心跳。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/extension.ts:L21–L39](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/extension.ts#L21-L39), [jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts:L145–L152](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts#L145-L152)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/extension.ts","start":21,"end":39,"sha256":"7dbf0613dd807298d8c0fc91dcaed3f3a5f9fd2300426883a824f73c580472fd"},{"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts","start":145,"end":152,"sha256":"d54bc92d0bccfc58b871aa0da6cfba59dbe09f5b197b7f5767102ab8f7ba6418"}],"trace":[]} -->
<!-- /kb:depth -->
