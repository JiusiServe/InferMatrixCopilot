---
title: "计划模式与多入口切换限制：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L115-L137, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L81-L99, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L54-L63, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L54-L70, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_plan_entry_source_contract.py:L84-L93, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/test_plan_entry_source_contract.py:L48-L57, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/permissionAnswerTransport.test.mjs:L43-L49, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/stores/planStore.ts:L76-L102, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L1-L19, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/stores/planStore.ts:L104-L108, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L54-L99]
feature: "plan-mode"
entry_points: ["jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts", "jiuwenswarm/channels/web/frontend/src/stores/planStore.ts"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts", "jiuwenswarm/channels/web/frontend/src/stores/planStore.ts"]
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

<!-- kb:depth feature=plan-mode facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=78e8730d856323f7efed6531d49a6743c2a3e06ab5a8ae8c5629375cfda478c5 -->
**applyPlanToggle 契约：返回 true 仅代表通过校验并调用了 setActive，不保证状态实际变化**
sessionId 为空或 evaluatePlanToggle 拒绝时返回 false（有 reason 则回调可选 onBlocked）；通过后按方向调 planStore.setActive 并返回 true。setActive 在新旧值一致时返回原 state，故 true 不代表 store 状态必然变化。

来源：[jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L115–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L115-L137), [jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L81–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L81-L99), [jiuwenswarm/channels/web/frontend/src/stores/planStore.ts:L76–L102](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/planStore.ts#L76-L102)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":137,"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","sha256":"aaa0ffe431c88a23759b5c87e4c1c35b6d020206183d5636de824930b33babbb","start":115},{"end":99,"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","sha256":"ab974ad286acd9a6b03b6136299ec4762cb65d996d2fc3175ce3bfc1c93559be","start":81},{"end":102,"path":"jiuwenswarm/channels/web/frontend/src/stores/planStore.ts","sha256":"5ccca34d4bb0cb8aa5cd4cde075705322867e6ef788bb8fc9ab1bcce2c6baae3","start":76}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plan-mode facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=43eca5a29773d36f2ee5657f49872a923b1b9160372594c3bff8e88c781354c1 -->
**开关默认值：applyPlanToggle 打开走 explicitEntry ?? true 与 PLAN_ENTRY_SOURCE_PLAN_TOGGLE；setActive 仅在 explicitEntry 为真时补 'plan_toggle' 缺省**
校验通过后 next=true 以 options.explicitEntry ?? true、options.entrySource ?? PLAN_ENTRY_SOURCE_PLAN_TOGGLE 调 setActive；next=false 调 setActive(sessionId, false) 不带 options。setActive 里 active=true 时已有 pending 值优先（|| 合并），仅当 options.explicitEntry 为真才写 entrySource（缺省 'plan_toggle'）；active=false 时 pendingExplicitEntry 复位 false、pendingEntrySource 复位 null，结果写入该会话 runtime 记录。

来源：[jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L115–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L115-L137), [jiuwenswarm/channels/web/frontend/src/stores/planStore.ts:L76–L102](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/planStore.ts#L76-L102)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":137,"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","sha256":"aaa0ffe431c88a23759b5c87e4c1c35b6d020206183d5636de824930b33babbb","start":115},{"end":102,"path":"jiuwenswarm/channels/web/frontend/src/stores/planStore.ts","sha256":"5ccca34d4bb0cb8aa5cd4cde075705322867e6ef788bb8fc9ab1bcce2c6baae3","start":76}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plan-mode facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b50f68e31ae75140d7770e36bb2499bb1bd134f8fc484d8453856dfae3b1b170 -->
**会话忙或（打开方向）存在未完成目标时 applyPlanToggle 返回 false 不调 setActive，仅回调可选 onBlocked(reason)**
evaluatePlanToggle：next=true 先拒未完成目标（'plan.toolbarUnavailableGoal'）再拒忙（'plan.toolbarUnavailableProcessing'）；next=false 仅忙时拒（'plan.closeTagDisabled'）。忙 = isProcessing || isPaused || pendingQuestions.length > 0（sessionId 或 runtime 缺失视为不忙）。被拒时 applyPlanToggle 本地返回 false、不调 planStore.setActive；decision.reason 存在才调用调用方提供的 options.onBlocked?.(reason)。

来源：[jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L54–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L54-L99), [jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L115–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L115-L137)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":99,"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","sha256":"b12ab069065fa80b17f05990aad33c4989692f970167e28385c3351ffd0268dc","start":54},{"end":137,"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","sha256":"aaa0ffe431c88a23759b5c87e4c1c35b6d020206183d5636de824930b33babbb","start":115}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plan-mode facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1b5694d77d78bf3632f986efa83fe33afa1e006871ef04943cafce9e755b3011 -->
**收益：单一忙口径可拦住等待期切换；成本：闸门非强制，planStore.toggle 仍直通 setActive**
设计推断（非作者历史意图）：

收益：忙口径含 isPaused 与 pendingQuestions，ask_user 等待期 isProcessing=false 时也能拦截（历史绕过仅由文件头注释记录，属文档性证据）。成本：拦截依赖入口自觉走闸门——planStore.toggle 直接 setActive({explicitEntry:true})，不经 evaluatePlanToggle。

来源：[jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L1–L19](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L1-L19), [jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L54–L63](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L54-L63), [jiuwenswarm/channels/web/frontend/src/stores/planStore.ts:L104–L108](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/planStore.ts#L104-L108)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":19,"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","sha256":"e8281e791a79c6cba2a5e90e080afc415530e89ef481c9d38c89aabbcf123146","start":1},{"end":63,"path":"jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts","sha256":"96116b422b2328e968d408e9879b0ea38bd547d534814b8df5fd6a1150d057ad","start":54},{"end":108,"path":"jiuwenswarm/channels/web/frontend/src/stores/planStore.ts","sha256":"63b658f7ff6807532039c627f212a698bb8ed706b440479b7c48f77a4be28cad","start":104}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=plan-mode facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=edc290837b65d52bc6e771900bc1c704b91a9cac7dcae2a075963b0c40663c59 -->
**pytest 用正则比对 Web planEntrySource.ts 字面量与后端常量（源文本级，非运行时集成）**
test_plan_toggle_literal_matches_web_ts 调 _extract_ts_const(_WEB_TS, 'PLAN_ENTRY_SOURCE_PLAN_TOGGLE')，以正则 export const NAME = 'literal' 抽取 Web 端 .ts 源文本字面量，断言与后端 PLAN_ENTRY_SOURCE_PLAN_TOGGLE == 相等（Python 端 rename 会使断言 fail）。该验证只比对源文件文本；planModeGate 闸门的前端运行时断言未出现在展示区间，permissionAnswerTransport.test.mjs 展示区间仅见 evaluatePlanToggle 的 import。

来源：[tests/unit_tests/test_plan_entry_source_contract.py:L84–L93](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_plan_entry_source_contract.py#L84-L93), [tests/unit_tests/test_plan_entry_source_contract.py:L48–L57](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/test_plan_entry_source_contract.py#L48-L57), [jiuwenswarm/channels/web/frontend/tests/permissionAnswerTransport.test.mjs:L43–L49](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/permissionAnswerTransport.test.mjs#L43-L49)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":93,"path":"tests/unit_tests/test_plan_entry_source_contract.py","sha256":"134c86a8e08aa07bdb3048058901c695050f46fe4f9968332d8a410a0da56800","start":84},{"end":57,"path":"tests/unit_tests/test_plan_entry_source_contract.py","sha256":"a4ed09f635bab2597460a4f7876784e7a2e3ca1dddc367b51095f67f91a93ee9","start":48},{"end":49,"path":"jiuwenswarm/channels/web/frontend/tests/permissionAnswerTransport.test.mjs","sha256":"b5adab497afc93a244044da22742154de64996201edba17087348880d4941a3f","start":43}],"trace":[],"validation_kind":"automated_source_text"} -->
<!-- /kb:depth -->
