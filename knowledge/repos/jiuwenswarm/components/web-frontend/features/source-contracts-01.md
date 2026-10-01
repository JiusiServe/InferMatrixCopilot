---
title: "features 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/agentIdentity.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3688479cd1094345698e90c42ab87f8dd7814135091bab4b62bbcae19a2bef42 -->
**`jiuwenswarm/channels/web/frontend/src/features/agentIdentity.ts`**

- 源码声明的类型、组件或调用边界：`normalizeAgentTemplateName`, `normalized`, `readAgentTemplateName`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/agentIdentity.ts#L1-L14)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/assetPublication.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3c2f5f23f8c1de184fe9227cfe30d3e10c887258bb6fd75ec23bc75282a9ff3c -->
**`jiuwenswarm/channels/web/frontend/src/features/assetPublication.ts`**

- 源码声明的类型、组件或调用边界：`PublicationState`, `PublicationFilter`, `matchesPublicationFilter`, `publicationLabel`, `labels`, `publicationDetailLabel`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/assetPublication.ts#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/assetPublishErrors.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=17ea1b0e194767157ce8800e66c09f4eefb1c7b8ab61c948ee9568ce574c488f -->
**`jiuwenswarm/channels/web/frontend/src/features/assetPublishErrors.ts`**

- 源码声明的类型、组件或调用边界：`SAFE_FAILURE_KEYS`, `PublishFailureKey`, `errorCode`, `candidate`, `payload`, `publishIssueKey`, `normalized`, `publishFailureKey`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/assetPublishErrors.ts#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/assetPublishEvents.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b014884785519b05dbc90594c2a58cf88c1475f99bb675fe62f0bae68bc20d26 -->
**`jiuwenswarm/channels/web/frontend/src/features/assetPublishEvents.ts`**

- 源码声明的类型、组件或调用边界：`openAssetPublish`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AssetPublishOpenRequest } from '../types/assetPublish';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/assetPublishEvents.ts#L1-L4)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2644c2818751998974e52674a67e615e3b4c6eb9efaa76d33fd69f3e567031d9 -->
**`jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts`**

- 源码声明的类型、组件或调用边界：`canShowAssetPublish`, `publishOutcome`, `result`, `validateMetadata`, `errors`, `createCommitAttempt`, `pending`, `completed`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { PublishMetadata, PublishRecord } from '../types/assetPublish';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/assetPublishState.ts#L1-L61)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/browserAgentActivity.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=876f522eac15d508e4e0e3bddce5bac8687345d4d22149cd6c86297925c6172c -->
**`jiuwenswarm/channels/web/frontend/src/features/browserAgentActivity.ts`**

- 源码声明的类型、组件或调用边界：`useBrowserAgentActivity`, `desktop`, `isTeam`, `active`, `receivedEvent`, `update`, `unsubscribe`, `hasBrowserSubagent`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { useSessionStore } from '../stores/sessionStore';`；`import { useSubagentStore } from '../stores/subagentStore';`；`import type { ElectronBrowserState } from '../types/electron';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/browserAgentActivity.ts#L1-L60)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/catalogCache.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7cb48c3245c5fec8f1c842538cfe923e26fa3c77f0fd5c4ee35165312858605a -->
**`jiuwenswarm/channels/web/frontend/src/features/catalogCache.ts`**

- 源码声明的类型、组件或调用边界：`CatalogCacheMetadata`, `CatalogCacheNoticeModel`, `catalogCacheNotice`, `failed`, `catalogCacheTimestamp`, `numeric`, `parsed`, `formatCatalogCacheUpdatedAt`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/catalogCache.ts#L1-L109)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/desktopBrowserFile.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=37d4c0c25dba2aaf4b8930361f6675073a9ba366dff4dd2c5a3238128b84f7ed -->
**`jiuwenswarm/channels/web/frontend/src/features/desktopBrowserFile.ts`**

- 源码声明的类型、组件或调用边界：`DESKTOP_BROWSER_TAB_EVENT`, `DESKTOP_BROWSER_TAB_FLAGS_KEY`, `DESKTOP_BROWSER_FILE_EXTENSIONS`, `DesktopBrowserTabFlags`, `EMPTY_TAB_FLAGS`, `tabFlagsStorageKey`, `loadDesktopBrowserTabFlags`, `raw`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { getApiBase } from '../utils/env';`；`import { useChatStore } from '../stores/chatStore';`；`import { useSessionStore } from '../stores/sessionStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/desktopBrowserFile.ts#L1-L128)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/equipmentListRequest.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=65226287977394a9ac277089c82b17a9722d94463ba9e86a666d35fb438d435a -->
**`jiuwenswarm/channels/web/frontend/src/features/equipmentListRequest.ts`**

- 源码声明的类型、组件或调用边界：`EquipmentListRequest`, `EQUIPMENT_LIST_TIMEOUT_MS`, `requestEquipmentList`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/equipmentListRequest.ts#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/equipmentMarketplace.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=67817c8eda30124856b907e8affea740be8c456562690cc72d4a361eaeff5846 -->
**`jiuwenswarm/channels/web/frontend/src/features/equipmentMarketplace.ts`**

- 源码声明的类型、组件或调用边界：`EquipmentKind`, `EquipmentScope`, `EquipmentSource`, `equipmentListFilter`, `equipmentListFilter`, `equipmentListFilter`, `normalizeEquipmentSource`, `normalizeEquipmentIdentity`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/equipmentMarketplace.ts#L1-L51)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/fileTreeFilters.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e0745b9d210c4dbd8d246b30bf4e88790ad6c5179d69e1bd1d05eb5674dad91a -->
**`jiuwenswarm/channels/web/frontend/src/features/fileTreeFilters.ts`**

- 源码声明的类型、组件或调用边界：`IGNORED_DIRECTORY_NAMES`, `IGNORED_DIRECTORY_SET`, `containsIgnoredDirectory`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/fileTreeFilters.ts#L1-L16)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/goalPendingObjectiveBubble.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=795610fffa3518b9fe2035ee9de2f2a80dd5610501a6b848039e7ebbb7887ecb -->
**`jiuwenswarm/channels/web/frontend/src/features/goalPendingObjectiveBubble.ts`**

- 源码声明的类型、组件或调用边界：`flushPendingGoalObjectiveBubble`, `queueOrAddGoalObjectiveMessage`, `trimmed`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useChatStore } from '../stores/chatStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/goalPendingObjectiveBubble.ts#L1-L26)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/historyFilePreview.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=65f1c13d7a49ae629f7be26457904b12a0d42dac039db439f41feb38051ed04e -->
**`jiuwenswarm/channels/web/frontend/src/features/historyFilePreview.ts`**

- 源码声明的类型、组件或调用边界：`isHistoryPreviewFile`, `lowerName`, `parseHistoryFileContent`, `trimmed`, `parsed`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/historyFilePreview.ts#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/historyPagination.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6ea072cf52f2139f37b01f796444f509bda304d578540451e929e3f10c9866b3 -->
**`jiuwenswarm/channels/web/frontend/src/features/historyPagination.ts`**

- 源码声明的类型、组件或调用边界：`HistoryCursorBatchDescriptor`, `HistoryCursorApplyState`, `HistoryCursorApplyCandidate`, `canApplyHistoryCursorBatch`, `filterPublishedHistoryBatch`, `HistoryPrefetchOutcome`, `PrefetchHistoryBatchesOptions`, `prefetchHistoryBatches`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/historyPagination.ts#L1-L121)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/historyRecordReassembler.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0bb22394782d8c7369c439856a8497e78ed7b91f3012e36a761d2f3d3be510aa -->
**`jiuwenswarm/channels/web/frontend/src/features/historyRecordReassembler.ts`**

- 源码声明的类型、组件或调用边界：`HistoryRecordReassembler`, `part`, `rid`, `idx`, `total`, `bucket`, `ordered`, `merged`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/historyRecordReassembler.ts#L1-L60)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/historyRestore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d7cd81c8fccb653758d55f65fdf12c119e649a54a66dfed4e190d3fbc7821ac -->
**`jiuwenswarm/channels/web/frontend/src/features/historyRestore.ts`**

- 源码声明的类型、组件或调用边界：`HISTORY_GET_METHOD`, `HISTORY_MESSAGE_EVENT`, `HISTORY_RESTORE_TIMEOUT_MS`, `ALLOWED_ASSISTANT_EVENT_TYPES`, `HISTORY_RESTORE_DONE_CONTENT`, `HistoryToolReplayItem`, `mergeHistoryToolReplayItems`, `merged`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { readOutputOrder, isSuppressedOutput } from './sessionOutput';`；`import type { OutputOrder } from '../types/message';`；`import { Message, MessageRole, UsageSummary, FileDownloadItem, MediaItem, WsEvent, ToolExecution, As`；`import { webClient } from '../services/webClient';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/historyRestore.ts#L1-L2582)。
<!-- /kb:file -->
