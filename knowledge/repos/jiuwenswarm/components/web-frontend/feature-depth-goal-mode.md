---
title: "持续目标与会话控制：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts:L201-L220, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts:L162-L182, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts:L126-L132, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts:L99-L102, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/webClient.ts:L747-L763, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/webClient.ts:L773-L792, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/webClient.ts:L340-L365]
feature: "goal-mode"
entry_points: ["jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts", "jiuwenswarm/channels/web/frontend/src/stores/goalStore.ts", "jiuwenswarm/channels/web/frontend/src/services/webClient.ts", "jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts", "jiuwenswarm/channels/web/frontend/src/stores/goalStore.ts", "jiuwenswarm/channels/web/frontend/src/services/webClient.ts", "jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts"]
---

# 持续目标与会话控制：实现深读

[功能概览](feature-goal-mode.md) · [owner 入口](_index.md)

<!-- kb:depth feature=goal-mode facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e55d267189e2a34be83902c15f806a08bc3bc65a8de2f4bfef8740d931d8a696 -->
**目标武装开关的闸门调用链：applyGoalArm → evaluateGoalArm → isGoalSessionBusy → hasPendingGoalAction**
用户在"+"菜单或 /goal 命令触发目标武装切换时，applyGoalArm 以 (sessionId, next) 为输入：先同步调用 evaluateGoalArm 做纯判定；关闭方向（next=false）时 evaluateGoalArm 调用 isGoalSessionBusy，后者再调用 hasPendingGoalAction 读取 useGoalStore 的 runtimes[sessionId].pendingAction。全部通过且 next=true 时，applyGoalArm 会把未提交的 Plan 关闭（planStore.setActive(sessionId, false)），最后 useGoalStore.setArmed(sessionId, next) 翻转武装位并返回 true；被拦截则回调 options.onBlocked(reason) 并返回 false。

调用路径：`jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts`（`applyGoalArm`） → `jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts`（`evaluateGoalArm`） → `jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts`（`isGoalSessionBusy`） → `jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts`（`hasPendingGoalAction`）

来源：[jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts:L201–L220](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts#L201-L220), [jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts:L162–L182](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts#L162-L182), [jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts:L126–L132](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts#L126-L132), [jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts:L99–L102](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts#L99-L102)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts","start":201,"end":220,"sha256":"a907c6d32fbc6bb0373c046f57c62d58efad72a9f98d8fcece99064a7bedecb1"},{"path":"jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts","start":162,"end":182,"sha256":"975e8fdd1626cce74b233761f50f8300ffa67e93362caf78f869111360126506"},{"path":"jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts","start":126,"end":132,"sha256":"a4143e6d6fc1a52ed5e2adf8eee4599ed7c845797cd29e3affce853bab09e10b"},{"path":"jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts","start":99,"end":102,"sha256":"9fea2377c8af0010269d4c1981c34f330a8e7a0fa075d73bdad748370625cdd1"}],"trace":[{"path":"jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts","symbol":"applyGoalArm","start":201,"end":220},{"path":"jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts","symbol":"evaluateGoalArm","start":162,"end":182},{"path":"jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts","symbol":"isGoalSessionBusy","start":126,"end":132},{"path":"jiuwenswarm/channels/web/frontend/src/features/goalMode/goalModeGate.ts","symbol":"hasPendingGoalAction","start":99,"end":102}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=goal-mode facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f6d35b8f953e1f08220bcbae836e1e575e80faae8ad86adb8dd488a5a52044c6 -->
**command.goal 的两种请求形态：一次性 res 与流式 fire-and-forget**
requestGoalAction（action 为 'get' | 'pause' | 'clear'）走 webRequest 等 res，action==='clear' 时直接返回 null（成功后 goal 视为已清空），否则取 payload.goal ?? payload.record；sendGoalStreamCommand（action 为 'set' | 'resume'）以 isStream:true 调 sendFireAndForget，不注册 pending、无超时，调用方义务是自行订阅 goal.snapshot/goal.updated 等事件获取真实状态。

来源：[jiuwenswarm/channels/web/frontend/src/services/webClient.ts:L747–L763](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/webClient.ts#L747-L763), [jiuwenswarm/channels/web/frontend/src/services/webClient.ts:L773–L792](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/webClient.ts#L773-L792), [jiuwenswarm/channels/web/frontend/src/services/webClient.ts:L340–L365](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/webClient.ts#L340-L365)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/services/webClient.ts","start":747,"end":763,"sha256":"8cedfd6cae8293d87b43314d71eb4939a1c728c555c7b74a36ac02583b40e5f2"},{"path":"jiuwenswarm/channels/web/frontend/src/services/webClient.ts","start":773,"end":792,"sha256":"dd71ccba83559e8cee9e186587136757fc25ee1297c8ec95e7b6c9b6147c5789"},{"path":"jiuwenswarm/channels/web/frontend/src/services/webClient.ts","start":340,"end":365,"sha256":"b8ee59b108fca9511326e463e23e7a688b0dcabeafec39cd8ae84314dad36f24"}],"trace":[]} -->
<!-- /kb:depth -->
