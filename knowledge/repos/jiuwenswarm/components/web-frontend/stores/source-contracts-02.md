---
title: "stores 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# stores 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/subagentStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=34314f9ef91b05c4a6706fbc501b1b4f78d2c403da12c7853603c314e62b281f -->
**`jiuwenswarm/channels/web/frontend/src/stores/subagentStore.ts`**

- 源码声明的类型、组件或调用边界：`SubagentRuntime`, `PERSISTED_RUNTIME_PREFIX`, `MAX_PERSISTED_ACTIVITIES`, `PersistedSubagentRuntime`, `SubagentState`, `createEmptySubagentRuntime`, `runtime`, `getStorage`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`；`import type { Subagent, SubagentActivity, SubagentEvent, SubagentResult, SubagentTurn, SubagentUpdat`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/subagentStore.ts#L1-L850)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/teamTaskNormalize.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=384f4fca7f9666ffb1eedc3819260d18dd76fc9dd131c286ab2e99d6dce4012d -->
**`jiuwenswarm/channels/web/frontend/src/stores/teamTaskNormalize.ts`**

- 源码声明的类型、组件或调用边界：`TEAM_TASK_STATUS_SET`, `normalizeTeamTaskStatus`, `pickString`, `value`, `normalizeStringArray`, `normalized`, `pickTruncationFlag`, `pickFiniteSize`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TeamTaskStatus, TeamTaskUpsert } from './sessionStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/teamTaskNormalize.ts#L1-L111)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/todoStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=86b45299668b4a5847982da8b45e54746c15e1d1c2518573ce99cbf943c9f171 -->
**`jiuwenswarm/channels/web/frontend/src/stores/todoStore.ts`**

- 源码声明的类型、组件或调用边界：`TodoRuntime`, `createEmptyRuntime`, `TodoState`, `useTodoStore`, `existing`, `runtime`, `next`, `runtime`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`；`import { TodoItem, TodoStatus } from '../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/todoStore.ts#L1-L170)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/toolResultLifecycle.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5c5122176c35303814a272ee77a012cfbc433975027d68fb55df4d2eb524e90d -->
**`jiuwenswarm/channels/web/frontend/src/stores/toolResultLifecycle.ts`**

- 源码声明的类型、组件或调用边界：`TERMINAL_REVIEWER_STATUSES`, `hasTerminalReviewer`, `status`, `terminalReviewerStatus`, `status`, `terminalReviewerDenied`, `status`, `mergeReviewerProgress`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { AutoReviewerMetadata, AutoReviewerStatus, ToolExecutionStatus, ToolResult } from '../types'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/toolResultLifecycle.ts#L1-L89)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/stores/workspaceStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aa2a6114427996ed358ded6a7b2eebed45a6bd7657b68b3245650845433332d3 -->
**`jiuwenswarm/channels/web/frontend/src/stores/workspaceStore.ts`**

- 源码声明的类型、组件或调用边界：`PROJECT_SESSION_PAGE_SIZE`, `DEFAULT_PROJECT_ID`, `DEFAULT_CODE_PROJECT_ID`, `normalizeProject`, `UpsertSessionOptions`, `WorkspaceState`, `findProject`, `isDefaultProject`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`；`import i18n from '../i18n';`；`import { projectRegistryClient, ProjectRemoveResult } from '../features/workspace/projectRegistryCli`；`import { archivedTaskClient, findBatchSessionResult } from '../features/workspace/archivedTaskClient`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/workspaceStore.ts#L1-L675)。
<!-- /kb:file -->
