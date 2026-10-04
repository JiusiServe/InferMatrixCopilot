---
title: "services 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# services 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4359db7cd214d65e7d6f7a20e90f8b3656d8f65d69765d2b7fe702c0821fc053 -->
**`jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts`**

- 源码声明的类型、组件或调用边界：`request`, `assetPublishApi`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { webRequest } from './webClient';`；`import { getStoredOAuthProvider, getStoredOAuthToken } from '../utils/gitcodeOAuth';`；`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/assetPublishApi.ts#L1-L40)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/services/authClient.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a7d5e95372c3f06b4bb511832a0c163b418745f9f3ed06e92b5aa89403612c0f -->
**`jiuwenswarm/channels/web/frontend/src/services/authClient.ts`**

- 源码声明的类型、组件或调用边界：`SESSION_HEADER`, `SESSION_STORAGE_KEY`, `AUTH_REQUEST_HEADER`, `AUTH_CALLBACK_CHANNEL`, `AUTH_CALLBACK_MESSAGE`, `AuthorizeResponse`, `CampaignState`, `AuthStatus`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { getApiBase } from '../utils/env';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/authClient.ts#L1-L286)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ef061f5120804cda7845bb3ff437b66f4b3064a9aff1d1d2d7ece52376bbb941 -->
**`jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts`**

- 源码声明的类型、组件或调用边界：`CatalogItems`, `RawConnectorSummary`, `fromRawSummary`, `identity`, `source`, `RawConnectorTool`, `RawConnectorDetail`, `fromRawDetail`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { withCatalogCache, type CatalogItems, type CatalogCacheMetadata } from '../features/catalogC`；`import { webRequest } from './webClient';`；`import type {`；`import { normalizeEquipmentIdentity, normalizeEquipmentSource } from '../features/equipmentMarketpla`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts#L1-L278)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/services/personalContextApi.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f07f604cdad35557f65f80456eb8bf8da37e67de2a588d40cbb7ce1d019f2a1e -->
**`jiuwenswarm/channels/web/frontend/src/services/personalContextApi.ts`**

- 源码声明的类型、组件或调用边界：`PersonalContextRuntimeState`, `FetchServiceState`, `FetchRunState`, `FetchItemError`, `FetchRunProgress`, `FetchRunRecord`, `FetchRunStatusService`, `FetchRunStatusResponse`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { webClient, webRequest } from './webClient';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/personalContextApi.ts#L1-L772)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/services/pluginPackagesApi.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ddbe8d9af352ca4cf7baf99a3efd9a8a3d925557d9939f593ad8d0b67ea13ed7 -->
**`jiuwenswarm/channels/web/frontend/src/services/pluginPackagesApi.ts`**

- 源码声明的类型、组件或调用边界：`CatalogItems`, `PluginInstallPendingError`, `RawPluginPackageSummary`, `fromRawSummary`, `RawPluginPackageDetail`, `fromRawDetail`, `extractPendingConnectors`, `payload`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { withCatalogCache, type CatalogItems, type CatalogCacheMetadata } from '../features/catalogC`；`import { webRequest } from './webClient';`；`import type { WebError } from '../types/websocket';`；`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/pluginPackagesApi.ts#L1-L174)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/services/sessionEventGate.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=612ee93c7948b043e48bbd7044b94aff60d8cc96efde6317037f7525e553c5fb -->
**`jiuwenswarm/channels/web/frontend/src/services/sessionEventGate.ts`**

- 源码声明的类型、组件或调用边界：`EventDispatcher`, `SuspendedSessionEvents`, `IMMEDIATE_SESSION_EVENTS`, `normalizeSessionId`, `isRecord`, `getEventSessionId`, `payload`, `direct`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { WsEvent } from '../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/sessionEventGate.ts#L1-L105)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/services/streamDeltaBatcher.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eb3ec7563ce307a4d1807f2fc86fcce3d80665ce546f601e2867fc92b23d5f00 -->
**`jiuwenswarm/channels/web/frontend/src/services/streamDeltaBatcher.ts`**

- 源码声明的类型、组件或调用边界：`TimerHandle`, `FlushCallback`, `StreamDeltaBatcherOptions`, `PendingDelta`, `createStreamDeltaBatcher`, `delayMs`, `schedule`, `cancel`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/streamDeltaBatcher.ts#L1-L62)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/services/webClient.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e475461899aa4ee6e3e83006aa98286be8fa0fd35e1fa97c48b0eb30e1f04e6a -->
**`jiuwenswarm/channels/web/frontend/src/services/webClient.ts`**

- 源码声明的类型、组件或调用边界：`EventHandler`, `TypedEventHandler`, `StateHandler`, `PendingRequest`, `MAX_RECONNECT_ATTEMPTS`, `DEFAULT_TIMEOUT_MS`, `LEGACY_EVENT_MAP`, `DevWsLogEntry`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import { getWsBase } from '../utils/env';`；`import { resolveUserId } from '../utils/userId';`；`import i18n from '../i18n';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/webClient.ts#L1-L799)。
<!-- /kb:file -->
