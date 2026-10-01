---
title: "stores 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# stores 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/agentCatalogStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4740816bddb84d741562e57c45917145841a15ad730dd56f3ee892bbcca04d09 -->
**`jiuwenswarm/channels/web/frontend/src/stores/agentCatalogStore.ts`**

- 源码声明的类型、组件或调用边界：`AgentCatalogStatus`, `AgentCatalogState`, `catalogGeneration`, `pendingLoad`, `useAgentCatalogStore`, `publishAgentCatalog`, `seedAgentCatalog`, `invalidateAgentCatalog`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`；`import type { AgentCatalogItem } from '../features/agentManagement/types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/agentCatalogStore.ts#L1-L79)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/agentGroupCatalogSeed.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eb028c168a1d1cf408cf05fcebd141f34c1c5a1e747f70e446d8fec2d72e236e -->
**`jiuwenswarm/channels/web/frontend/src/stores/agentGroupCatalogSeed.ts`**

- 源码声明的类型、组件或调用边界：`selectedGroup`, `seedSelectedAgentGroup`, `getSelectedAgentGroup`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AgentGroupCatalogItem } from '../features/agentManagement/types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/agentGroupCatalogSeed.ts#L1-L11)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/authStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fed2ffecba156d04eeaada65e3c4c785ba84b03d4629536d002f53c090b70790 -->
**`jiuwenswarm/channels/web/frontend/src/stores/authStore.ts`**

- 源码声明的类型、组件或调用边界：`RETRY_DELAYS_MS`, `DEFAULT_ACCOUNT_CENTER_URL`, `LoginPhase`, `AuthState`, `pendingLogin`, `detachTriggers`, `claimInFlight`, `claimRequestedAgain`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`；`import { webClient } from '../services/webClient';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/authStore.ts#L1-L425)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/chatStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=90b469d68c643e5682d3464c20dda1a6d4506c6c12c1fe65e8080efba5a3469d -->
**`jiuwenswarm/channels/web/frontend/src/stores/chatStore.ts`**

- 源码声明的类型、组件或调用边界：`TOOL_TIMEOUT_MS`, `EVOLUTION_STATUS_END_VISIBLE_MS`, `reasoningSegmentSeq`, `createReasoningSegmentId`, `computeTimeoutAt`, `resolveExecutionStatus`, `TaskInputStatus`, `TaskInputReceipt`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`；`import { subscribeWithSelector } from 'zustand/middleware';`；`import {`；`import { useTodoStore } from './todoStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/chatStore.ts#L1-L2188)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/connectorStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d29c1e296eea8036db4caccdf9589f0d06509c9b979b3804ff31aa3cd95fdbd4 -->
**`jiuwenswarm/channels/web/frontend/src/stores/connectorStore.ts`**

- 源码声明的类型、组件或调用边界：`ConnectorState`, `patchConnection`, `patchConnectionAll`, `mergeByName`, `map`, `item`, `invalidateDetail`, `next`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { scheduleCatalogRefresh, catalogScope } from '../features/catalogCache';`；`import { create } from 'zustand';`；`import i18n from '../i18n';`；`import { connectorApi } from '../services/connectorApi';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/connectorStore.ts#L1-L621)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/cronStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=830f43d1a0d813496ac1c829bfb83939ef1c4ba0eb9abac9b630f6f206fa5996 -->
**`jiuwenswarm/channels/web/frontend/src/stores/cronStore.ts`**

- 源码声明的类型、组件或调用边界：`SidebarCronJob`, `isWebChannelJob`, `s`, `CronState`, `persistCronUnread`, `useCronStore`, `value`, `next`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`；`import { webRequest } from '../services/webClient';`；`import { projectRegistryClient } from '../features/workspace/projectRegistryClient';`；`import type { Session } from '../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/cronStore.ts#L1-L165)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/ensureSessionRuntimes.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=52ff199d983992b024e9622fa6f5c5eca45d8c8206465228329f20e5f9296bb0 -->
**`jiuwenswarm/channels/web/frontend/src/stores/ensureSessionRuntimes.ts`**

- 源码声明的类型、组件或调用边界：`ensureSessionRuntimes`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useChatStore } from './chatStore';`；`import { useGoalStore } from './goalStore';`；`import { useHarnessStore } from './harnessStore';`；`import { usePlanStore } from './planStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/ensureSessionRuntimes.ts#L1-L15)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/goalStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a0fbd67d78c15b60b43273b14a561d8b6d87506d57c951d87c227f3d910a2a7e -->
**`jiuwenswarm/channels/web/frontend/src/stores/goalStore.ts`**

- 源码声明的类型、组件或调用边界：`GoalRuntime`, `createEmptyRuntime`, `LOCAL_CREATED_AT_STORAGE_KEY`, `LOCAL_CREATED_AT_MAX_ENTRIES`, `loadLocalCreatedAtFromStorage`, `raw`, `parsed`, `saveLocalCreatedAtToStorage`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`；`import { GoalAction, GoalRecord } from '../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/goalStore.ts#L1-L401)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/harnessStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cd458e8300d7fd88e2e7ff963a98a1cbbdb2586cf141d90db581509105c1edff -->
**`jiuwenswarm/channels/web/frontend/src/stores/harnessStore.ts`**

- 源码声明的类型、组件或调用边界：`HarnessStageStatus`, `ExtensionProgressStatus`, `HarnessStageDefinition`, `HarnessStageInfo`, `HarnessMessageEntry`, `ExtensionReadyInfo`, `RuntimeExtensionInfo`, `ExtensionProgressInfo`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/harnessStore.ts#L1-L550)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/pendingQuestionQueue.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7b4136da3c94c8f3009b0a70251f979d58f8e3641cd63ba6d97f5a30a571b8f8 -->
**`jiuwenswarm/channels/web/frontend/src/stores/pendingQuestionQueue.ts`**

- 源码声明的类型、组件或调用边界：`PERMISSION_SOURCES`, `boundedIdentity`, `normalized`, `pendingQuestionIdentity`, `kind`, `requestId`, `permissionQuestionKind`, `enqueuePendingQuestions`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/pendingQuestionQueue.ts#L1-L95)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/personalContextStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=434e95aa9023219a85b9ee761e69a7cfdf1512418f15d691889181d766a2a1b6 -->
**`jiuwenswarm/channels/web/frontend/src/stores/personalContextStore.ts`**

- 源码声明的类型、组件或调用边界：`AuthorizationResult`, `ContextGraph`, `FetchServiceConfig`, `FetchServicePatch`, `FetchProvider`, `FetchRunRecord`, `PersonalContextConfig`, `PersonalContextStatus`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/personalContextStore.ts#L1-L499)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/planStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0263b25e971d690d52c2256ada688465791c2e7ff2247d8af378d740ffe2643e -->
**`jiuwenswarm/channels/web/frontend/src/stores/planStore.ts`**

- 源码声明的类型、组件或调用边界：`PlanRuntime`, `createEmptyRuntime`, `SetActiveOptions`, `PlanState`, `usePlanStore`, `runtimes`, `current`, `pendingExplicitEntry`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/planStore.ts#L1-L133)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/pluginPackageStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=76418fccc1c0e19235bc039362691eaf7370e1e0d8b4283bbaa784d55ae81668 -->
**`jiuwenswarm/channels/web/frontend/src/stores/pluginPackageStore.ts`**

- 源码声明的类型、组件或调用边界：`LOCAL_STORAGE_KEY`, `PersistedLocalState`, `loadPersistedLocalState`, `raw`, `parsed`, `persistLocalState`, `PluginPackageState`, `persisted`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { scheduleCatalogRefresh, catalogScope } from '../features/catalogCache';`；`import { create } from 'zustand';`；`import { extractRpcErrorMessage } from '../features/agentManagement/upload';`；`import { PluginInstallPendingError, pluginPackagesApi } from '../services/pluginPackagesApi';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/pluginPackageStore.ts#L1-L384)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/sessionStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4cac560f1a108e54268a40b8c8377bc4fcc2b7535213e2f8ec30f7e320c79274 -->
**`jiuwenswarm/channels/web/frontend/src/stores/sessionStore.ts`**

- 源码声明的类型、组件或调用边界：`TaskProgressBaseline`, `TeamConnectionPresentation`, `WorkflowAgent`, `WorkflowPhase`, `WorkflowRun`, `TeamLeaderIdentity`, `MODE_STORAGE_KEY`, `MODEL_STORAGE_KEY`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`；`import {`；`import {`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/sessionStore.ts#L1-L1968)。
<!-- /kb:file -->
