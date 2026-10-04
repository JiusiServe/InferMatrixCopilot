---
title: "components-teamarea 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-teamarea 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/UnassignedTeamAvatar.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f558676aa17c78f707c1df545562da5aa1cee7143a10ec042afea1621cd9d006 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/UnassignedTeamAvatar.tsx`**

- 源码声明的类型、组件或调用边界：`UnassignedTeamAvatar`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/UnassignedTeamAvatar.tsx#L1-L16)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5d9ff4a0d18cbf8eacaefa1085c45706e68067091ae22a9df8e296d384c0d4d4 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/index.tsx`**

- 源码声明的类型、组件或调用边界：`useTaskPlanningMetrics`, `activeSessionId`, `todos`, `teamTaskEvents`, `teamTasks`, `taskProgressBaseline`, `progressTasks`, `timer`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useMemo, useState } from 'react';`；`import { useChatStore, useSessionStore, useTodoStore } from '../../stores';`；`import { normalizeTaskStatus } from './shared';`；`import { getTasksForCurrentProgress } from '../../features/teamTaskProgressBaseline';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/index.tsx#L1-L54)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/shared.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5456511a84d9ffe2a532fcef25c868068036a130c463f7de08ea3d69938eb3e6 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/shared.tsx`**

- 源码声明的类型、组件或调用边界：`Translate`, `TeamMember`, `TeamTaskEvent`, `MemberTask`, `ProcessDetailRow`, `ProcessItem`, `BaseTeamAreaProps`, `TeamAreaProps`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { ChevronRight, Circle } from 'lucide-react';`；`import CheckIcon from '../../assets/work-mode/check.svg?react';`；`import i18n from '../../i18n';`；`import { ParsedTeamEvent, parseTeamEventMessage } from '../ChatPanel/teamEventUtils';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/shared.tsx#L1-L590)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/taskProgress.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=afb320aa7138bae24f16e71173b8c7f036c72ed9ad21d7abdb71ea43f3aa498d -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/taskProgress.ts`**

- 源码声明的类型、组件或调用边界：`RUNNING_PROGRESS_INITIAL`, `RUNNING_PROGRESS_CAP`, `RUNNING_PROGRESS_EASING_MS`, `getTaskStartTime`, `getTaskVisualProgressPercent`, `clock`, `elapsedMs`, `eased`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TeamTask } from '../../stores/sessionStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/taskProgress.ts#L1-L58)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/workflowTypes.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=40b49275e73cf1ef2e60cdb860e02c4c284f439b6ef9f89c2a68a98f46eff9c6 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/workflowTypes.ts`**

- 源码声明的类型、组件或调用边界：`WorkflowStatus`, `WorkflowNodeType`, `WorkflowAgentActivity`, `WorkflowBudget`, `compactTokenLabel`, `k`, `m`, `formatBudgetK`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/workflowTypes.ts#L1-L971)。
<!-- /kb:file -->
