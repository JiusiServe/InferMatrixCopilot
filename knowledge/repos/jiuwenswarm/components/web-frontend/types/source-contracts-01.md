---
title: "types 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# types 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/assetPublish.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a903e8a99979042687bae3461efa245d4176fd842bcb7552b5a8238f9f0a394a -->
**`jiuwenswarm/channels/web/frontend/src/types/assetPublish.ts`**

- 源码声明的类型、组件或调用边界：`PublishAssetKind`, `AssetReference`, `AssetPublishOpenRequest`, `PublishMetadata`, `PublishIssue`, `PublishRecord`, `PublishDescription`, `PublishDraft`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/assetPublish.ts#L1-L47)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/beamSearch.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9124a093d2e5c86d13357ae9bc4bcb2e02dae3771f6d761e4616574a84acaa52 -->
**`jiuwenswarm/channels/web/frontend/src/types/beamSearch.ts`**

- 源码声明的类型、组件或调用边界：`BeamNodeStatus`, `BeamSearchNode`, `BeamSearchEdge`, `BeamSearchGraph`, `BeamSearchProgress`, `asRecord`, `parseBeamSearchProgress`, `record`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/beamSearch.ts#L1-L48)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/connector.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=35111469903e84f34715d8d004e72fa43614fc2a1a8b694e43d2a5624bc71991 -->
**`jiuwenswarm/channels/web/frontend/src/types/connector.ts`**

- 源码声明的类型、组件或调用边界：`ConnectorIntegrationType`, `ConnectorConnectionState`, `ConnectorSource`, `McpBusyKind`, `ConnectorSummary`, `ConnectorInstallResponse`, `ConnectorUninstallResponse`, `ConnectorTool`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/connector.ts#L1-L138)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/contextUsage.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d7ff523658c2d3109a064f46be4b963d4192c0fbece54852c705a50fc96a5f8e -->
**`jiuwenswarm/channels/web/frontend/src/types/contextUsage.ts`**

- 源码声明的类型、组件或调用边界：`ContextUsagePart`, `ContextUsageSnapshot`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/contextUsage.ts#L1-L28)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/cron.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9805e3cffa3703a60966f1384e2d21e4161cd47d37d02c10d9aebb200a735895 -->
**`jiuwenswarm/channels/web/frontend/src/types/cron.ts`**

- 源码声明的类型、组件或调用边界：`CronJobDTO`, `CronTaskUI`, `CronTemplateUI`, `CronScheduleKind`, `CronSchedule`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AgentMode } from './index';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/cron.ts#L1-L67)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/electron.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=18f6125139b7ac24465a3c88f9edf5be6269cc6bc791d6f2a4ead7b7459a3487 -->
**`jiuwenswarm/channels/web/frontend/src/types/electron.ts`**

- 源码声明的类型、组件或调用边界：`ElectronBrowserState`, `ElectronBrowserBounds`, `JiuwenElectronDesktopApi`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/electron.ts#L1-L72)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/goal.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d1036f697e3aaf36ebd17fc1057bf6886418dec39c90dabb1816ef951be413f2 -->
**`jiuwenswarm/channels/web/frontend/src/types/goal.ts`**

- 源码声明的类型、组件或调用边界：`GoalStatus`, `GoalTokenUsage`, `GoalAssessment`, `GoalRecord`, `GoalAction`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/goal.ts#L1-L45)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/heartbeat.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=803151b2739be1dc7bc31a3bfb16cf73fbf04b4e0d35fbee95331cf70fffb442 -->
**`jiuwenswarm/channels/web/frontend/src/types/heartbeat.ts`**

- 源码声明的类型、组件或调用边界：`HeartbeatJobStatus`, `HeartbeatRunStatus`, `HeartbeatConcurrencyPolicy`, `HeartbeatSessionDeletedPolicy`, `HeartbeatScheduleKind`, `HeartbeatScheduleDTO`, `HeartbeatAutomationMetadata`, `HeartbeatRunState`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/heartbeat.ts#L1-L139)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/index.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=53fb4cbf2556ddfae2ebeec65a6dcff1f689a69888ac89a68cf8af4f6647723d -->
**`jiuwenswarm/channels/web/frontend/src/types/index.ts`**

- 源码声明的类型、组件或调用边界：`Session`, `AgentMode`, `SessionStatus`, `Permission`, `ModelPlan`, `ModelReasoningCapability`, `ModelReasoningProtocols`, `ModelReasoningRule`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/index.ts#L1-L187)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/message.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=abc7c2757f6d66945a234875ad8f7ad34f9610edc14a61c53717163203109902 -->
**`jiuwenswarm/channels/web/frontend/src/types/message.ts`**

- 源码声明的类型、组件或调用边界：`MessageRole`, `OutputOrder`, `MediaItem`, `UsageSummary`, `FileDownloadItem`, `AutoReviewerStatus`, `AutoReviewerMetadata`, `ContextCompressionRuntime`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { SkillTreePath } from './skillTree';`；`import type { BeamSearchProgress } from './beamSearch';`；`import type { HeartbeatAutomationMetadata } from './heartbeat';`；`import type { CrossSessionMessageMetadata } from '../utils/crossSessionMessage';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/message.ts#L1-L244)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/pluginPackage.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aa87b7fd48119171f61bce2e08ca4770d5613bf427a7ef7eb30a976b90dbe8cb -->
**`jiuwenswarm/channels/web/frontend/src/types/pluginPackage.ts`**

- 源码声明的类型、组件或调用边界：`LocalizedText`, `PluginPackageSource`, `PluginConnectionState`, `PluginPackageSummary`, `PluginCapabilityRef`, `PluginPackageDetail`, `localizedText`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/pluginPackage.ts#L1-L83)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/skillTree.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=66788942bd7def492512669e5651c051aa176422dd34f6c28623771c689a70fe -->
**`jiuwenswarm/channels/web/frontend/src/types/skillTree.ts`**

- 源码声明的类型、组件或调用边界：`SkillTreeNamedId`, `SkillTreeEventType`, `SkillTreeStep`, `SkillTreeCandidate`, `SkillTreePath`, `asRecord`, `parseSkillTreePath`, `source`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`source = JSON.parse(source);`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/skillTree.ts#L1-L98)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/subagent.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ab59ea389336e6ddecbb7a28eed8aae6c5836ca7c17668f3fc7790955ee62263 -->
**`jiuwenswarm/channels/web/frontend/src/types/subagent.ts`**

- 源码声明的类型、组件或调用边界：`SubagentStatus`, `SubagentTurnOutcome`, `SubagentLifecycle`, `SubagentClosedReason`, `SubagentActivityKind`, `SubagentError`, `Subagent`, `SubagentActivity`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/subagent.ts#L1-L83)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/todo.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8399785e1cf3da3e2711a04ce390d11125273bd4dc0ef96c83878429c3ea3b99 -->
**`jiuwenswarm/channels/web/frontend/src/types/todo.ts`**

- 源码声明的类型、组件或调用边界：`TodoStatus`, `TodoItem`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/todo.ts#L1-L16)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/types/websocket.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1b01ab472223a78e825c688eea7652eb9cf79f0b1a52795cb7d7822d57d38d38 -->
**`jiuwenswarm/channels/web/frontend/src/types/websocket.ts`**

- 源码声明的类型、组件或调用边界：`WebConnectionState`, `WsRequest`, `WsResponse`, `WsEvent`, `WebMessage`, `WebRequestOptions`, `WebConnectOptions`, `WebError`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AutoReviewerMetadata } from './message';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/types/websocket.ts#L1-L204)。
<!-- /kb:file -->
