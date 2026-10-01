---
title: 计划模式与多入口切换限制的职责、接口与配置
created: '2026-10-01'
updated: '2026-10-01'
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/stores/planStore.ts
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/模式系统.md
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/Harness.md
---

# 计划模式与多入口切换限制的职责、接口与配置

本页提供该能力的基本知识与验证入口，固定基线 `f0a69728c96b`。

<!-- kb:knowledge owner=feature-plan-mode facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

Web 计划模式把每个会话的开关与进入来源保存在 planStore，planModeGate 汇总 UI、标签和斜杠命令的用户切换判断。后端退出事件与刷新恢复属于状态同步，直接更新 store；客户端开关状态仍需与后端模式装配核对，不能用亮起的按钮代替服务端已接受计划请求。

源码与文档：[jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L1–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L1-L137)；[jiuwenswarm/channels/web/frontend/src/stores/planStore.ts:L1–L133](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/planStore.ts#L1-L133)；[docs/zh/模式系统.md:L1–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L1-L263)；[docs/zh/Harness.md:L1–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L1-L626)。

<!-- kb:knowledge owner=feature-plan-mode facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

isSessionBusyForPlanToggle 将执行中、暂停中和等待用户回答统一为会话忙；evaluatePlanToggle 检查打开和关闭方向，applyPlanToggle 通过判断后更新 store 并可回调阻断原因。显式进入可携带 plan_toggle 或 slash_command 来源；后端 plan.mode_exited 事件更新状态而不经过用户操作判断。

源码与文档：[jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L1–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L1-L137)；[jiuwenswarm/channels/web/frontend/src/stores/planStore.ts:L1–L133](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/planStore.ts#L1-L133)；[docs/zh/模式系统.md:L1–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L1-L263)；[docs/zh/Harness.md:L1–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L1-L626)。

<!-- kb:knowledge owner=feature-plan-mode facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

计划运行状态按 sessionId 保存，进入选项包含 explicitEntry 与 entrySource。打开方向同时检查未完成 Goal 和会话忙，关闭方向检查会话忙；pendingQuestions 非空时即使 isProcessing 已为 false 仍受保护，暂停也不表示回合结束。这里的配置入口是会话控制选项，不是新增 YAML 字段。

源码与文档：[jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L1–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L1-L137)；[jiuwenswarm/channels/web/frontend/src/stores/planStore.ts:L1–L133](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/planStore.ts#L1-L133)；[docs/zh/模式系统.md:L1–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L1-L263)；[docs/zh/Harness.md:L1–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L1-L626)。

<!-- kb:knowledge owner=feature-plan-mode facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：集中切换判断能让图形按钮与命令拥有同样行为，但必须把用户操作与后端状态同步分开。只使用 isProcessing 会遗漏等人回答的窗口；只依赖客户端开关又会忽略刷新和服务端退出，因此调用方要维护来源、会话和后端事件的一致性。

源码与文档：[jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L1–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L1-L137)；[jiuwenswarm/channels/web/frontend/src/stores/planStore.ts:L1–L133](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/planStore.ts#L1-L133)；[docs/zh/模式系统.md:L1–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L1-L263)；[docs/zh/Harness.md:L1–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L1-L626)。

<!-- kb:knowledge owner=feature-plan-mode facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

用户显式进入计划模式后发送需求，计划请求与执行交给现有模式和 Harness 链路，退出事件再更新会话界面。它关联任务规划与 Todo，但客户端 Plan 开关不是通用 Todo 工具；与 Goal 的互斥规则保护同一会话中的持续执行意图。

源码与文档：[jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L1–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L1-L137)；[jiuwenswarm/channels/web/frontend/src/stores/planStore.ts:L1–L133](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/planStore.ts#L1-L133)；[docs/zh/模式系统.md:L1–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L1-L263)；[docs/zh/Harness.md:L1–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L1-L626)。

<!-- kb:knowledge owner=feature-plan-mode facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

对菜单、标签关闭和斜杠命令分别检查同一限制，覆盖执行、暂停、等待回答及未完成目标。确认进入来源被记录，后端退出、刷新恢复和新会话迁移能同步状态，再核对计划请求实际选用模式。本页未声明上游模式测试已运行。

源码与文档：[jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts:L1–L137](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/planMode/planModeGate.ts#L1-L137)；[jiuwenswarm/channels/web/frontend/src/stores/planStore.ts:L1–L133](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/stores/planStore.ts#L1-L133)；[docs/zh/模式系统.md:L1–L263](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%A8%A1%E5%BC%8F%E7%B3%BB%E7%BB%9F.md#L1-L263)；[docs/zh/Harness.md:L1–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Harness.md#L1-L626)。

关联阅读：[goal-mode](feature-goal-mode.md)；[planning](../agents-team/feature-planning.md)；[modes](../agent-server-runtime/feature-modes.md)；[web-chat](feature-web-chat.md)。
