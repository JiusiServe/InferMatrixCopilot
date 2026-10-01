---
title: "components-goalbar 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-goalbar 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/GoalBar/EditGoalModal.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e9ae61718fce9db5a10d1a5bf1fd4abeb6974e1f117e0c0444c8c3ed712c5efb -->
**`jiuwenswarm/channels/web/frontend/src/components/GoalBar/EditGoalModal.tsx`**

- 源码声明的类型、组件或调用边界：`EditGoalModalProps`, `EditGoalModal`, `canSave`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`；`import { Target, X } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/GoalBar/EditGoalModal.tsx#L1-L73)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/GoalBar/GoalCompletedCard.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7223a525a668f21abbfdb101ca3bce127aee8b0db987c0b8301c4cd8a270e648 -->
**`jiuwenswarm/channels/web/frontend/src/components/GoalBar/GoalCompletedCard.tsx`**

- 源码声明的类型、组件或调用边界：`GoalCompletedCardProps`, `GoalCompletedCard`, `data`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Target } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import { parseGoalCompletedContent } from './goalCompletedMessage';`；`import './GoalBar.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/GoalBar/GoalCompletedCard.tsx#L1-L35)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/GoalBar/OverwriteGoalConfirmModal.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9e79f9320f57084ac5433d1ac2f63a6800cf57e52f12f001041f36b88e657416 -->
**`jiuwenswarm/channels/web/frontend/src/components/GoalBar/OverwriteGoalConfirmModal.tsx`**

- 源码声明的类型、组件或调用边界：`OverwriteGoalConfirmModalProps`, `OverwriteGoalConfirmModal`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`；`import { Target, X } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/GoalBar/OverwriteGoalConfirmModal.tsx#L1-L85)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/GoalBar/goalCompletedMessage.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2215cc5ebad9062113425d1f62baeabf0c2535484f66a957eb2bdf8282ae571a -->
**`jiuwenswarm/channels/web/frontend/src/components/GoalBar/goalCompletedMessage.ts`**

- 源码声明的类型、组件或调用边界：`GOAL_COMPLETED_PREFIX`, `GoalCompletedData`, `buildGoalCompletedContent`, `isGoalCompletedContent`, `parseGoalCompletedContent`, `raw`, `parsed`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/GoalBar/goalCompletedMessage.ts#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/GoalBar/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1788c1e919985b03eb918f1ae6a8a01d39fa3e6f5723d1eb0341e5f2f929169d -->
**`jiuwenswarm/channels/web/frontend/src/components/GoalBar/index.tsx`**

- 源码声明的类型、组件或调用边界：`GoalBarProps`, `DisplayTone`, `STATUS_TONE`, `formatSeconds`, `seconds`, `minutes`, `remainSeconds`, `formatElapsedFallback`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Pause, Pencil, Play, Target, Trash2 } from 'lucide-react';`；`import { useChatStore, useGoalStore, useSessionStore } from '../../stores';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/GoalBar/index.tsx#L1-L247)。
<!-- /kb:file -->
