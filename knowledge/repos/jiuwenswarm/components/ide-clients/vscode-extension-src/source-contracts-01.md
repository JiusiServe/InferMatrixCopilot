---
title: "vscode-extension-src 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# vscode-extension-src 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/client/SessionManager.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7c598180011d657b22739f40001260a26fdc5ca636a2afc0d956920f5b1c1b05 -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/client/SessionManager.ts`**

- 源码声明的类型、组件或调用边界：`PendingRequest`, `REQUEST_TIMEOUT_SEC`, `SessionManager`, `idx`, `payload`, `models`, `activeModel`, `payload`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { WsClient } from './WsClient';`；`import { JiuwenMessage, SessionInfo, makeRequest } from './protocol';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/client/SessionManager.ts#L1-L265)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dc6a8280eca733f121172d3500b1f220e4ae0ceac1cccbe1985916e94f3e8d05 -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts`**

- 源码声明的类型、组件或调用边界：`WsStatus`, `WsEventMap`, `BACKOFF_MS`, `DEFAULT_PING_INTERVAL_MS`, `WsClient`, `arr`, `idx`, `arr`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import WebSocket from 'ws';`；`import { JiuwenMessage } from './protocol';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/client/WsClient.ts#L1-L161)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/client/protocol.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=328c932aa7afc1157a295e88426453d47972120e9b2de16e59a625813f750fea -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/client/protocol.ts`**

- 源码声明的类型、组件或调用边界：`JiuwenMessage`, `SessionInfo`, `ExtToWebviewMsg`, `SessionMetrics`, `ModelEntry`, `SkillEntry`, `WebviewToExtMsg`, `randomId`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/client/protocol.ts#L1-L122)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/codeActions/FixWithAiCodeActionProvider.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ee371ebe04b53ef387997dbc94c36ca546d8c14a8d1832d1bf7416be32b53dae -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/codeActions/FixWithAiCodeActionProvider.ts`**

- 源码声明的类型、组件或调用边界：`FixWithAiCodeActionProvider`, `diagnostics`, `action`, `buildDiagnosticPrefill`, `primary`, `line`, `errorText`, `startLine`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import * as vscode from 'vscode';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/codeActions/FixWithAiCodeActionProvider.ts#L1-L67)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/context/ContextCollector.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9207e73b71d9f78b45aa8dc3b357a1a13553683ddbf8f434ba0e1221b7af7ad6 -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/context/ContextCollector.ts`**

- 源码声明的类型、组件或调用边界：`ContextMetrics`, `CollectedContext`, `collectContext`, `editor`, `filePath`, `lang`, `selection`, `diagnostics`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import * as vscode from 'vscode';`；`import { execSync } from 'child_process';`；`import * as path from 'path';`；`import * as fs from 'fs';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/context/ContextCollector.ts#L1-L329)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5a2e66030d197d3840d4f4199bf72ae313fa0ad200b7314bbf4a6c02fe9ba8da -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts`**

- 源码声明的类型、组件或调用边界：`EDIT_TOOLS`, `FileSnapshot`, `currentTurnSnapshots`, `lastTurnSnapshots`, `clearSnapshots`, `promoteSnapshots`, `getLastTurnSnapshots`, `clearLastTurnSnapshots`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import * as vscode from 'vscode';`；`import * as path from 'path';`；`import * as fs from 'fs';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L1-L294)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffViewer.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=281e98ccc084bbc617fa2099bb105ab582c45b87002dd650dfae3856e326036b -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffViewer.ts`**

- 源码声明的类型、组件或调用边界：`DIFF_SCHEME`, `DiffDocumentProvider`, `uri`, `provider`, `registerDiffProvider`, `showDiffAndPrompt`, `fileName`, `originalUri`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import * as vscode from 'vscode';`；`import * as fs from 'fs';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffViewer.ts#L1-L120)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/swarm/SwarmMapPanel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4ddaa5f8c6b3005b92c4244415425168b44e29d89e065487c46e48df6d39864c -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/swarm/SwarmMapPanel.ts`**

- 源码声明的类型、组件或调用边界：`SwarmMapPanel`, `pendingLines`, `line`, `htmlPath`, `html`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import * as vscode from 'vscode';`；`import * as fs from 'fs';`；`import * as path from 'path';`；`import { SwarmSnapshot } from './SwarmState';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/swarm/SwarmMapPanel.ts#L1-L115)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/swarm/SwarmState.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=70c8e710f377e927b18b61fe0e60b3681f65a77cc63a3d42fa161718fd0428fa -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/swarm/SwarmState.ts`**

- 源码声明的类型、组件或调用边界：`LaneFeedEntry`, `AgentLane`, `TeamTask`, `TeamMessage`, `SwarmSnapshot`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/swarm/SwarmState.ts#L1-L47)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/swarm/SwarmStateManager.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c52f99ada3f1482189a50c72db80d437ff5ab5f468f7f34e2eb362d2cccda1d2 -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/swarm/SwarmStateManager.ts`**

- 源码声明的类型、组件或调用边界：`SwarmStateManager`, `root`, `event`, `type`, `teamName`, `e`, `lane`, `activity`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import * as path from 'path';`；`import { AgentLane, TeamTask, TeamMessage, SwarmSnapshot } from './SwarmState';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/swarm/SwarmStateManager.ts#L1-L448)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=35482335c39eacb953bbe0613b08b763764a97b45f38370112abb335326285c3 -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts`**

- 源码声明的类型、组件或调用边界：`activeTerminal`, `runCommand`, `disposeTerminal`, `extractCommand`, `args`, `command`, `extractArguments`, `tc`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import * as vscode from 'vscode';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/terminal/TerminalManager.ts#L1-L65)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9dcae198560d0c192e8ed9070a3cec12a0c3d905ca201fe4110e612d925d26db -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts`**

- 源码声明的类型、组件或调用边界：`ChatPanel`, `statusListener`, `msgListener`, `sessionListener`, `type`, `content`, `mode`, `rid`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import * as vscode from 'vscode';`；`import * as fs from 'fs';`；`import * as path from 'path';`；`import { execSync } from 'child_process';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts#L1-L1128)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/StatusBar.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=05d60e718a185b06666ec5420483162329a0dbb1f877d00f2e603e12c3c7a7e5 -->
**`jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/StatusBar.ts`**

- 源码声明的类型、组件或调用边界：`StatusBar`, `tokenLabel`, `contextLabel`, `costLabel`, `metricsTooltip`, `formatTokenCount`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import * as vscode from 'vscode';`；`import { WsClient, WsStatus } from '../client/WsClient';`；`import { SessionMetrics } from '../client/protocol';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/StatusBar.ts#L1-L91)。
<!-- /kb:file -->
