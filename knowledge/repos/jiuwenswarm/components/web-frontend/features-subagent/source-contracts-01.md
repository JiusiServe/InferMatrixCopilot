---
title: "features-subagent 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-subagent 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/subagent/subagentActivityPresentation.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e9729b3ada64d0b576c9e41ac6193b60e1d7e0e0e148341760f23268d3f3976d -->
**`jiuwenswarm/channels/web/frontend/src/features/subagent/subagentActivityPresentation.ts`**

- 源码声明的类型、组件或调用边界：`SubagentActivityGroup`, `SubagentTaskStatus`, `SubagentTaskStatusChange`, `SubagentTask`, `firstNonEmptyLine`, `boundedPreview`, `line`, `unescapeQuotedValue`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { SubagentActivity } from '../../types/subagent';`；`source: SubagentTaskStatusChange['source'],`；`const source: SubagentTaskStatusChange['source'] = toolName.includes('create')`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/subagent/subagentActivityPresentation.ts#L1-L306)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/subagent/subagentNormalizer.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=52db7edd0860da19e2e0c0d60203059f9c0a25c12057fef23a386397ca9fa4dc -->
**`jiuwenswarm/channels/web/frontend/src/features/subagent/subagentNormalizer.ts`**

- 源码声明的类型、组件或调用边界：`RecordValue`, `ACTIVITY_KINDS`, `asRecord`, `asString`, `asNumber`, `asNonNegativeInteger`, `number`, `normalizeLifecycle`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/subagent/subagentNormalizer.ts#L1-L317)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/subagent/subagentStatusPresentation.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c671f19913e8fc43bd56b2791f58b947b327d6e78853a194abc764430bf67ea9 -->
**`jiuwenswarm/channels/web/frontend/src/features/subagent/subagentStatusPresentation.ts`**

- 源码声明的类型、组件或调用边界：`SubagentStatusTone`, `getSubagentStatusTone`, `getSubagentStatusLabelKey`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { SubagentClosedReason, SubagentStatus, SubagentTurnOutcome } from '../../types/subagent`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/subagent/subagentStatusPresentation.ts#L1-L32)。
<!-- /kb:file -->
