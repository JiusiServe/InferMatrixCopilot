---
title: "background 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# background 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/background/ContextCache.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=66c3bd09e6c3309f799d3072f9399b259bf2e576169eb8d66eb9bfd09b36c3ce -->
**`jiuwenswarm/channels/browser/frontend/src/background/ContextCache.ts`**

- 源码声明的类型、组件或调用边界：`ContextCache`, `parts`, `total`, `id`, `ctx`, `header`, `block`, `remaining`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { PageContext } from "@shared/types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/ContextCache.ts#L1-L57)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/background/ContextMenu.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4bd3de01e14125880baa1e1d28d40dc3b2cd4b1b23816aa8ce12829626a1b989 -->
**`jiuwenswarm/channels/browser/frontend/src/background/ContextMenu.ts`**

- 源码声明的类型、组件或调用边界：`log`, `MENU_ASK`, `MENU_PIN`, `MENU_SUMMARIZE`, `MENU_READER`, `MENU_SEARCH`, `DynamicMenuApi`, `dynMenu`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createLogger } from "@shared/logger";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/ContextMenu.ts#L1-L149)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/background/PanelManager.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d82247e68742af2310041301121ab5b4a5d78e3cd2a6fa4a1f0751982ebe2e7a -->
**`jiuwenswarm/channels/browser/frontend/src/background/PanelManager.ts`**

- 源码声明的类型、组件或调用边界：`log`, `PANEL_URL`, `hasSidePanel`, `_popupWindowId`, `openPanel`, `win`, `tracked`, `onRemoved`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createLogger } from "@shared/logger";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/PanelManager.ts#L1-L76)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/background/SessionManager.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f2d4adde5c24371389c77595c022e37cdec784028a4b9eaeadcb82e5b600030d -->
**`jiuwenswarm/channels/browser/frontend/src/background/SessionManager.ts`**

- 源码声明的类型、组件或调用边界：`log`, `ServerSessionRow`, `ChangeListener`, `SessionManager`, `n`, `payload`, `rows`, `payload`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createLogger } from "@shared/logger";`；`import { loadActiveSessionId, saveActiveSessionId, loadSessionDisplayNames, saveSessionDisplayName }`；`import { ResearchSession } from "@shared/types";`；`import { GW_METHOD } from "@shared/protocol";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/SessionManager.ts#L1-L202)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/background/TabWatcher.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c843fb05121581030063632debe29666a0d7788b9b05d1a33e0c5443ee86605a -->
**`jiuwenswarm/channels/browser/frontend/src/background/TabWatcher.ts`**

- 源码声明的类型、组件或调用边界：`log`, `TabWatcher`, `cached`, `age`, `response`, `response`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createLogger } from "@shared/logger";`；`import { MSG } from "@shared/constants";`；`import type { ContextCache } from "./ContextCache";`；`import type { PageContext } from "@shared/types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/TabWatcher.ts#L1-L93)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/background/ToolDispatcher.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=89456f7493098abaf62d3fdd6a8d068aeda03f5893e5104cfc60a605aae0fb24 -->
**`jiuwenswarm/channels/browser/frontend/src/background/ToolDispatcher.ts`**

- 源码声明的类型、组件或调用边界：`log`, `ToolDispatcher`, `result`, `tab`, `resp`, `tab`, `tab`, `tab`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createLogger } from "@shared/logger";`；`import { InboundEnvelope, GW_METHOD } from "@shared/protocol";`；`import { MSG } from "@shared/constants";`；`import { addPinnedPage } from "@shared/storage";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/ToolDispatcher.ts#L1-L277)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/background/WsClient.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b4c89ab9bc253bdb493754caee0d50ba6a94bf310b5a545ea7537eab6a5fa0f6 -->
**`jiuwenswarm/channels/browser/frontend/src/background/WsClient.ts`**

- 源码声明的类型、组件或调用边界：`EventHandler`, `StatusChangeHandler`, `log`, `BACKOFF_MS`, `PendingRequest`, `REQUEST_TIMEOUT_MS`, `WsClient`, `settings`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createLogger } from "@shared/logger";`；`import { InboundEnvelope, makeRequest, GW_EVENT } from "@shared/protocol";`；`import { loadSettings } from "@shared/storage";`；`import { WS_URL } from "@shared/constants";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/background/WsClient.ts#L1-L230)。
<!-- /kb:file -->
