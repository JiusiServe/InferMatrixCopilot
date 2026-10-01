---
title: "features-planmode 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-planmode 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/planMode/planEntrySource.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c6cb6f528608b1e6ec06390e8b4fe5b152180d80fb6684434111156ff68fb895 -->
**`jiuwenswarm/channels/web/frontend/src/features/planMode/planEntrySource.ts`**

- 源码声明的类型、组件或调用边界：`PLAN_ENTRY_SOURCE_PLAN_TOGGLE`, `PLAN_ENTRY_SOURCE_SLASH_COMMAND`, `PLAN_ENTRY_SOURCES`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planEntrySource.ts#L1-L43)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cf2b25dcf55c2e730200a99cc757a47f3082a5e36c250f44d5924ed0d1341cf9 -->
**`jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts`**

- 源码声明的类型、组件或调用边界：`PlanToggleBlockReason`, `PlanToggleDecision`, `isSessionBusyForPlanToggle`, `runtime`, `sessionHasUnfinishedGoal`, `goal`, `evaluatePlanToggle`, `busy`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useChatStore } from '../../stores/chatStore';`；`import { useGoalStore } from '../../stores/goalStore';`；`import { usePlanStore } from '../../stores/planStore';`；`import { hasUnfinishedGoal } from '../../components/ChatPanel/slashCommands/semantics';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L1-L137)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/planMode/wireMode.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c0110ce1342a6156322cec00354052d3889b672fdde413761772ddaddc12708b -->
**`jiuwenswarm/channels/web/frontend/src/features/planMode/wireMode.ts`**

- 源码声明的类型、组件或调用边界：`PlanBaseMode`, `PlanWorkProfile`, `supportsPlanMode`, `isTeamAgentMode`, `normalized`, `resolvePlanWireMode`, `base`, `env`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/wireMode.ts#L1-L106)。
<!-- /kb:file -->
