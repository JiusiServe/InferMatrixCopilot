---
title: "multi-session-state 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# multi-session-state 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/state/createConversationSession.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cd3366ea096a7c330907559f2bd53bdb25ff56658732fc59e0391a7ef4425936 -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/state/createConversationSession.ts`**

- 源码声明的类型、组件或调用边界：`SESSION_CREATE_TIMEOUT_MS`, `SESSION_CREATE_METADATA_POLL_ATTEMPTS`, `SESSION_CREATE_METADATA_POLL_INTERVAL_MS`, `SessionCreateRequestFn`, `SessionCreatePayload`, `CreatedConversationSession`, `CreateConversationSessionOptions`, `PersistSessionCommand`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { WorkMode } from '../../features/workspace/projectTypes';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/state/createConversationSession.ts#L1-L135)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/state/newConversationLifecycle.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=45f4607d7fc1d046ad01dbe3b3250d89181f3579041c51a36bfe122c3cf6ad08 -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/state/newConversationLifecycle.ts`**

- 源码声明的类型、组件或调用边界：`NEW_CONVERSATION_ID`, `ConversationRuntimeSettings`, `NewConversationEntrySettings`, `resolveNewConversationEntrySettings`, `locallyCreatedConversations`, `createConversationTitle`, `applyRuntimeSettings`, `resetNewConversationRuntime`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import type { AgentMode, Session } from '../../types';`；`import { toDisplaySessionTitle } from '../../utils/documentMessage';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/state/newConversationLifecycle.ts#L1-L131)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/state/newConversationPreviousSession.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e31661850784fd70e39fb553b724a9e4d79da8cb184a5acaf20d8f8b1dd1f643 -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/state/newConversationPreviousSession.ts`**

- 源码声明的类型、组件或调用边界：`PendingPreviousSession`, `ResolvePendingPreviousSessionOptions`, `resolvePendingPreviousSession`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AgentMode } from '../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/state/newConversationPreviousSession.ts#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/state/newConversationProject.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c4e0485a09841777543249e44b8125b7cbd2fe02c153bb75fff5814e57d7e1a3 -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/state/newConversationProject.ts`**

- 源码声明的类型、组件或调用边界：`resolveNewConversationProjectDir`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/state/newConversationProject.ts#L1-L8)。
<!-- /kb:file -->
