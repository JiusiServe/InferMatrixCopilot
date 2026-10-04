---
title: "utils 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# utils 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/chatFinalProtocol.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=451728e160725b4bd1fb7aacc243b82429cae60f58965fde214279fe2044c42a -->
**`jiuwenswarm/channels/web/frontend/src/utils/chatFinalProtocol.ts`**

- 源码声明的类型、组件或调用边界：`ChatFinalMode`, `ChatFinalAction`, `A2UI_OPEN_TAG`, `contentHasA2UIBlock`, `parseChatFinalMode`, `raw`, `mode`, `parseChatFinalSegmentId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { collapseWs } from './finalContent';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/chatFinalProtocol.ts#L1-L138)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/contextCompression.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b0d91bca94b5bc279039ff4114d34f9eda798211a808c165dae482fa7c1e341c -->
**`jiuwenswarm/channels/web/frontend/src/utils/contextCompression.ts`**

- 源码声明的类型、组件或调用边界：`contextCompressionRunningText`, `key`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/contextCompression.ts#L1-L22)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/crossSessionMessage.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=640a973e90a9b96ba58738855162df357435c87d6d1ba6f48bd7bade0c30202b -->
**`jiuwenswarm/channels/web/frontend/src/utils/crossSessionMessage.ts`**

- 源码声明的类型、组件或调用边界：`CROSS_SESSION_MESSAGE_ORIGIN`, `CrossSessionMessageMetadata`, `readString`, `extractCrossSessionMessage`, `raw`, `crossSession`, `messageId`, `sourceSessionId`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/crossSessionMessage.ts#L1-L53)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/desktopSave.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1add977a7c2fad06e5983f1cc27cf220edc94a780dc7b2f12f183dc4e2a60c46 -->
**`jiuwenswarm/channels/web/frontend/src/utils/desktopSave.ts`**

- 源码声明的类型、组件或调用边界：`DesktopSaveResult`, `DesktopSaveApiResult`, `DesktopSaveOutcome`, `BlobSaveTransport`, `BlobSaveResult`, `BlobSaveOptions`, `BrowserWritableFileStream`, `BrowserFileHandle`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/desktopSave.ts#L1-L201)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/documentMessage.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0e62742137bc3af36ac24fd707b095d6a92e2d35fc34575217945ecc922aa323 -->
**`jiuwenswarm/channels/web/frontend/src/utils/documentMessage.ts`**

- 源码声明的类型、组件或调用边界：`UPLOAD_DOCUMENT_BLOCK_HEADER`, `UploadDocumentHint`, `formatAtPath`, `stripUploadDocumentBlocks`, `toDisplaySessionTitle`, `withUploadDocumentBlock`, `base`, `lines`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/documentMessage.ts#L1-L87)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/enabledExtensions.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5ff31eef7d0e1b69f0792d1d61cc54842173085df6677415a9642e44df9faf2e -->
**`jiuwenswarm/channels/web/frontend/src/utils/enabledExtensions.ts`**

- 源码声明的类型、组件或调用边界：`pruneEnabledExtensions`, `sessionStore`, `runtime`, `mcpConnectionByName`, `plugins`, `id`, `installedState`, `connectionState`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useSessionStore } from '../stores/sessionStore';`；`import { usePluginPackageStore } from '../stores/pluginPackageStore';`；`import { useConnectorStore } from '../stores/connectorStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/enabledExtensions.ts#L1-L91)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/env.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3e7e7d6431ec783e173a8446397282e39f31711582df794675997973387b8eb6 -->
**`jiuwenswarm/channels/web/frontend/src/utils/env.ts`**

- 源码声明的类型、组件或调用边界：`normalizeBase`, `getApiBase`, `desktopApiBase`, `raw`, `getWsBase`, `desktopWsBase`, `raw`, `apiBase`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/env.ts#L1-L27)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/fileDownloadDedup.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1bd79440b3dbcaba2b25b38c1d0ccd9dd5fb890236f16c9c85233df83deb47cd -->
**`jiuwenswarm/channels/web/frontend/src/utils/fileDownloadDedup.ts`**

- 源码声明的类型、组件或调用边界：`FileIdentitySource`, `decodeBase64UrlUtf8`, `base64`, `padded`, `binary`, `bytes`, `getTokenPayload`, `payloadPart`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/fileDownloadDedup.ts#L1-L138)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/finalContent.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ee69f8a698916efd6e0245a51c684f7f6a233a2c795b5bbb5dd4fa190709f5dd -->
**`jiuwenswarm/channels/web/frontend/src/utils/finalContent.ts`**

- 源码声明的类型、组件或调用边界：`unescapeLiteralNewlines`, `realNl`, `litNl`, `normalizeFinalDisplayText`, `collapseWs`, `resolveStreamFinalContent`, `streamedN`, `finalN`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/finalContent.ts#L1-L118)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/formatters.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5ba9fd281e89df5de3d6c471f493838f37558e78af6e0bef5764ac3626ee204d -->
**`jiuwenswarm/channels/web/frontend/src/utils/formatters.ts`**

- 源码声明的类型、组件或调用边界：`formatTimestamp`, `date`, `pad`, `dateStr`, `timeStr`, `formatDate`, `date`, `formatRelativeTime`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import i18n from '../i18n';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/formatters.ts#L1-L73)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/frontendPlatform.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=718bb08de8e6c2db55e113c1e9eecc5b99558c26e66ff8bf32a8d9c772d273cc -->
**`jiuwenswarm/channels/web/frontend/src/utils/frontendPlatform.ts`**

- 源码声明的类型、组件或调用边界：`FrontendPlatform`, `SidebarNavKey`, `DEFAULT_FRONTEND_PLATFORM`, `PLATFORM_ALIASES`, `HIDDEN_NAV_ITEMS_BY_PLATFORM`, `normalizeFrontendPlatform`, `key`, `resolveFrontendPlatform`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/frontendPlatform.ts#L1-L57)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/gitcodeOAuth.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4d3c183cb996cedbd1d54c4f42fbcee5b600c4572ddf2c681e82d53ef23dfb0c -->
**`jiuwenswarm/channels/web/frontend/src/utils/gitcodeOAuth.ts`**

- 源码声明的类型、组件或调用边界：`TOKEN_KEY`, `PROVIDER_KEY`, `USER_KEY`, `AUTHORIZATION_CLOSE_GRACE_MS`, `OAuthProvider`, `HubOAuthAttempt`, `OAuthUser`, `responseJson`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/gitcodeOAuth.ts#L1-L125)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/heartbeatAutomation.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=25e851e6b832d7bbac1f4c38295a005b17cf210cefeb59336f41eddfee53b626 -->
**`jiuwenswarm/channels/web/frontend/src/utils/heartbeatAutomation.ts`**

- 源码声明的类型、组件或调用边界：`extractAutomation`, `meta`, `automation`, `parsed`, `normalizeAutomation`, `obj`, `jobId`, `runId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { HeartbeatAutomationMetadata } from '../types/heartbeat';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/heartbeatAutomation.ts#L1-L86)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/mySkills.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fe21f1265e9152d2d67fca1c0d9a3ca61285bb1a3b05b651f10cc3050cf77851 -->
**`jiuwenswarm/channels/web/frontend/src/utils/mySkills.ts`**

- 源码声明的类型、组件或调用边界：`computeMySkills`, `installed`, `isCandidate`, `buildInstalledSkillNames`, `set`, `plugin`, `skill`, `isSkillInstalled`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/mySkills.ts#L1-L64)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/proactiveRecommendation.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=164bb78afb2d2edb4e90dd6d31bd8a1784c020ebea1770beb7c5c90210b437d3 -->
**`jiuwenswarm/channels/web/frontend/src/utils/proactiveRecommendation.ts`**

- 源码声明的类型、组件或调用边界：`proactiveAssistantMessageId`, `clean`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/proactiveRecommendation.ts#L1-L11)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/skillAvatar.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e9c560f0b8261f850d6c05edcab96634697e067ecba74cee2be964b2281de2d6 -->
**`jiuwenswarm/channels/web/frontend/src/utils/skillAvatar.ts`**

- 源码声明的类型、组件或调用边界：`avatarPalette`, `AvatarStyle`, `hexToRgba`, `r`, `g`, `b`, `getSkillAvatar`, `trimmed`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { CSSProperties } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/skillAvatar.ts#L1-L47)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/utils/skillNetUrl.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1a76fcd3eb4c6e4791950ca96423c95ecf245d2a2d4c792ae351a554accf7dc1 -->
**`jiuwenswarm/channels/web/frontend/src/utils/skillNetUrl.ts`**

- 源码声明的类型、组件或调用边界：`normalizeSkillNetUrl`, `s`, `u`, `path`, `buildClawHubOrigin`, `s`, `owner`, `isClawHubOriginInstalled`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/utils/skillNetUrl.ts#L1-L127)。
<!-- /kb:file -->
