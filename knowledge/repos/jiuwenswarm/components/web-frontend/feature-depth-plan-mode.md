---
title: "计划模式与多入口切换限制：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L115-L137, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L81-L99, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L54-L63, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L54-L70]
---

# 计划模式与多入口切换限制：实现深读

[功能概览](feature-plan-mode.md) · [owner 入口](_index.md)

<!-- kb:depth feature=plan-mode facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=733dfcb9ffee763f1a8bc831e61275260065f777f667353480cb19f4fef3bb2c -->
**用户切换计划模式的统一闸门链路**
任意用户入口调用 applyPlanToggle(sessionId, next)：它先调 evaluatePlanToggle 判断目标状态是否允许；evaluatePlanToggle 内部调 isSessionBusyForPlanToggle 读取 chatStore 中该会话的 isProcessing/isPaused/pendingQuestions。校验通过后 applyPlanToggle 才 ensureRuntime 并调 planStore.setActive 翻转开关；被拦下时通过 options.onBlocked 回传原因并返回 false。

调用路径：`jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts`（`applyPlanToggle`） → `jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts`（`evaluatePlanToggle`） → `jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts`（`isSessionBusyForPlanToggle`）

来源：[jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L115–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L115-L137), [jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L81–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L81-L99), [jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L54–L63](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L54-L63)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","start":115,"end":137,"sha256":"aaa0ffe431c88a23759b5c87e4c1c35b6d020206183d5636de824930b33babbb"},{"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","start":81,"end":99,"sha256":"ab974ad286acd9a6b03b6136299ec4762cb65d996d2fc3175ce3bfc1c93559be"},{"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","start":54,"end":63,"sha256":"96116b422b2328e968d408e9879b0ea38bd547d534814b8df5fd6a1150d057ad"}],"trace":[{"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","symbol":"applyPlanToggle","start":115,"end":137},{"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","symbol":"evaluatePlanToggle","start":81,"end":99},{"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","symbol":"isSessionBusyForPlanToggle","start":54,"end":63}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plan-mode facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e28ee43986594c26941ec6d9eeb171fc7f6c1013ab57830d92a27487fe4bca4c -->
**闸门对 chatStore 与 goalStore 的耦合**
isSessionBusyForPlanToggle 直接读 useChatStore.getState().runtimes[sessionId] 的 isProcessing/isPaused/pendingQuestions 三个信号；sessionHasUnfinishedGoal 读 useGoalStore 的 goal 并交给 hasUnfinishedGoal 判定（打开方向命中时返回 'plan.toolbarUnavailableGoal'）。这使计划开关的限制口径依赖会话与目标两个 store 的运行时状态。

来源：[jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L54–L70](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L54-L70), [jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L81–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L81-L99)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","start":54,"end":70,"sha256":"6cf3b4c7040103259ed4babc20c152b20d32a18546933e7b5f3ad406afae9d1c"},{"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","start":81,"end":99,"sha256":"ab974ad286acd9a6b03b6136299ec4762cb65d996d2fc3175ce3bfc1c93559be"}],"trace":[]} -->
<!-- /kb:depth -->
