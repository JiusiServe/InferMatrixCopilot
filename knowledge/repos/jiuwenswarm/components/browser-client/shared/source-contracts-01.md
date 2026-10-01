---
title: "shared 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# shared 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/shared/constants.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3c470205ce7d0db210873031e6030eeeb9bec3c1eabd149587e70c4426a1b94d -->
**`jiuwenswarm/channels/browser/frontend/src/shared/constants.ts`**

- 源码声明的类型、组件或调用边界：`DEFAULT_HOST`, `DEFAULT_PORT`, `CHANNEL_ID`, `APP_ID`, `WS_URL`, `STORAGE_KEYS`, `MAX_PINNED_PAGES`, `MAX_CONTEXT_CHARS`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/shared/constants.ts#L1-L81)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/shared/i18n.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7f17767926cce6c83d0b7a6831a01c328fa7de4b6103149d5ece7dbcc2cd0ed4 -->
**`jiuwenswarm/channels/browser/frontend/src/shared/i18n.ts`**

- 源码声明的类型、组件或调用边界：`Dict`, `EN`, `ZH`, `_dict`, `initI18n`, `lang`, `t`, `applyStaticI18n`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/shared/i18n.ts#L1-L250)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/shared/logger.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=256a7caa6e4709db3d8ba869492d798008d12793120576471f6928bbdbed74ad -->
**`jiuwenswarm/channels/browser/frontend/src/shared/logger.ts`**

- 源码声明的类型、组件或调用边界：`LogLevel`, `LEVEL_RANK`, `IS_PROD`, `MIN_LEVEL`, `Logger`, `line`, `createLogger`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/shared/logger.ts#L1-L72)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/shared/messages.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=12e6e29683b2df962e91511a3177850b4cac41dc18d32db3485a85b353db40b5 -->
**`jiuwenswarm/channels/browser/frontend/src/shared/messages.ts`**

- 源码声明的类型、组件或调用边界：`SidePanelRequest`, `SidePanelAction`, `RequestOf`, `BackgroundReply`, `replyKey`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { MSG } from "./constants";`；`import { PinnedPage, ResearchSession } from "./types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/shared/messages.ts#L1-L62)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/shared/protocol.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6089ce175f825e9de6a1168d60ebc7c38e44f88a56c13204c9e9370fb5d504bf -->
**`jiuwenswarm/channels/browser/frontend/src/shared/protocol.ts`**

- 源码声明的类型、组件或调用边界：`GW_METHOD`, `GW_EVENT`, `WsRequest`, `ChatParams`, `ToolResultParams`, `makeRequest`, `InboundMsgType`, `InboundEnvelope`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { CHANNEL_ID } from "./constants";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/shared/protocol.ts#L1-L137)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/shared/storage.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=50e87d9a093a8b2abf7715d6c0ccd18e6bbb9353dc2281732e1274a79e597979 -->
**`jiuwenswarm/channels/browser/frontend/src/shared/storage.ts`**

- 源码声明的类型、组件或调用边界：`loadActiveSessionId`, `result`, `saveActiveSessionId`, `loadPinnedPages`, `result`, `savePinnedPages`, `addPinnedPage`, `pages`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { STORAGE_KEYS } from "./constants";`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/shared/storage.ts#L1-L168)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/shared/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=952530d8dfd693120f37ec1773ac84202288106ee27f88062d71f087c95b6b54 -->
**`jiuwenswarm/channels/browser/frontend/src/shared/types.ts`**

- 源码声明的类型、组件或调用边界：`PageMeta`, `PageContext`, `PinnedPage`, `ResearchSession`, `ChatEntry`, `ExtensionSettings`, `DEFAULT_SETTINGS`, `PageContextMsg`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/shared/types.ts#L1-L116)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/shared/url.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e58ad64e28dedebc064c04b753c87a928fd6d5cbee1e0ced9bce8ca720d58ea5 -->
**`jiuwenswarm/channels/browser/frontend/src/shared/url.ts`**

- 源码声明的类型、组件或调用边界：`normalizeUrl`, `u`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/shared/url.ts#L1-L10)。
<!-- /kb:file -->
