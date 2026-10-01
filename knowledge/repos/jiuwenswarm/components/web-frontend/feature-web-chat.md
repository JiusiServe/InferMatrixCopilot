---
title: Web 对话与流式状态 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/对话.md
---

# Web 对话与流式状态 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-web-chat facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

Web 客户端管理消息输入、流式展示与运行状态，后端负责真正的会话执行。界面显示的状态需要和服务端事件、会话标识一起解释。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L1–L5652](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts#L1-L5652)；[docs/zh/对话.md:L1–L312](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%AF%B9%E8%AF%9D.md#L1-L312)。

<!-- kb:knowledge owner=feature-web-chat facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `applyToolUpdatePayload`；`streamDeltaBatchKey`；`ensureCrossSessionUserTurn`；`isCompletedResumeResult`；`scheduleAfterTurnSettles`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L1–L5652](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts#L1-L5652)；[docs/zh/对话.md:L1–L312](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%AF%B9%E8%AF%9D.md#L1-L312)。

<!-- kb:knowledge owner=feature-web-chat facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

配置与启用条件的权威入口是下列功能文档和实现的调用方。本页提供查证路由：先确认当前宿主、会话或运行模式，再检查文档中的操作条件与实现消费的输入；不把 UI 文案、文件名或方法名猜作可写配置键。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L1–L5652](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts#L1-L5652)；[docs/zh/对话.md:L1–L312](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%AF%B9%E8%AF%9D.md#L1-L312)。

<!-- kb:knowledge owner=feature-web-chat facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：Web 前端通过流式事件展示执行过程，让用户在长任务中观察与补充要求；代价是界面需要处理连接和运行状态的异步变化。消息显示完成、最终执行结果与后台资源清理不是同一个事件，取消应沿请求和会话身份验证。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L1–L5652](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts#L1-L5652)；[docs/zh/对话.md:L1–L312](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%AF%B9%E8%AF%9D.md#L1-L312)。

<!-- kb:knowledge owner=feature-web-chat facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

Web 客户端管理消息输入、流式展示与运行状态，后端负责真正的会话执行。界面显示的状态需要和服务端事件、会话标识一起解释。 联调时结合[Web 页面与功能入口](feature-web-navigation.md)、[项目、会话与历史管理](../agent-runtime/feature-projects-sessions.md)、[E2A 统一请求响应协议](../protocols/feature-e2a.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L1–L5652](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts#L1-L5652)；[docs/zh/对话.md:L1–L312](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%AF%B9%E8%AF%9D.md#L1-L312)。

<!-- kb:knowledge owner=feature-web-chat facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

发送带工具调用的任务，检查消息流、工具状态和最终结果关联到同一会话。覆盖发送中断、断连恢复、执行中补充要求和取消，验证切换视图后返回仍能解释当前运行状态。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts:L1–L5652](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useWebSocket.ts#L1-L5652)；[docs/zh/对话.md:L1–L312](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%AF%B9%E8%AF%9D.md#L1-L312)。
