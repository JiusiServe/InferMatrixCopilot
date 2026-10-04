---
title: "features-chattimeline 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-chattimeline 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/chatTimeline/buildTurnTimeline.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0707454d5e24274d1737e82cb4aa6dd55eeb9ca26f6b030de0a569f43be20447 -->
**`jiuwenswarm/channels/web/frontend/src/features/chatTimeline/buildTurnTimeline.ts`**

- 源码声明的类型、组件或调用边界：`legacyMessageKeyCache`, `legacyMessageKeyCounter`, `getMessageRenderKey`, `key`, `TimelineItem`, `RenderItem`, `toTimestampMs`, `getTimelineOutputOrder`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { Message, OutputOrder, ToolExecution } from '../../types';`；`import type { ReasoningSegment } from '../../stores/chatStore';`；`import { getMessageActor } from '../../components/ChatPanel/MessageItem';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/chatTimeline/buildTurnTimeline.ts#L1-L1149)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/chatTimeline/index.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d94aaa7062c233c9f2a2d8aac471862745a514830d8a2c98e22e89af322530d8 -->
**`jiuwenswarm/channels/web/frontend/src/features/chatTimeline/index.ts`**

- 源码声明的类型、组件或调用边界：`TimelineItem`, `RenderItem`, `TurnWorkMeta`, `LiveWorkStreak`, `WorkOutcomeTone`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/chatTimeline/index.ts#L1-L26)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/chatTimeline/projectTimelineItems.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ed78f8333b75abe550e3614c28e3d3d00f6c6980a23dcf0743d88cecca9c2bb2 -->
**`jiuwenswarm/channels/web/frontend/src/features/chatTimeline/projectTimelineItems.ts`**

- 源码声明的类型、组件或调用边界：`projectTimelineItems`, `turnKeys`, `streakByItemKey`, `item`, `streak`, `key`, `meta`, `turnKey`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { RenderItem, LiveWorkStreak, TurnWorkMeta } from './buildTurnTimeline';`；`import { filterDeliverableExecutions } from './buildTurnTimeline';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/chatTimeline/projectTimelineItems.ts#L1-L59)。
<!-- /kb:file -->
