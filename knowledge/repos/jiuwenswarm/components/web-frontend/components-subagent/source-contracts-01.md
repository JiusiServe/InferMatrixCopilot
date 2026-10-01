---
title: "components-subagent 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-subagent 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/subagent/SubagentCompactPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9784891f26e9851a2ae7fc20413fcbaa3a383ec852cecda7447f87b5c03b225b -->
**`jiuwenswarm/channels/web/frontend/src/components/subagent/SubagentCompactPanel.tsx`**

- 源码声明的类型、组件或调用边界：`SubagentCompactPanel`, `runtime`, `setSelectedSubagent`, `subagents`, `statusLabel`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import { useSubagentStore, selectSubagents } from '../../stores/subagentStore';`；`import { getSubagentStatusLabelKey } from '../../features/subagent/subagentStatusPresentation';`；`import CollapseIcon from '../../assets/subagent/collapse.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/subagent/SubagentCompactPanel.tsx#L1-L60)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/subagent/SubagentExpandedPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2434ecde0fa0c5275e05caee7f6ed3f67bddeb761f0fa2d38c04ba1b8ed5a6cc -->
**`jiuwenswarm/channels/web/frontend/src/components/subagent/SubagentExpandedPanel.tsx`**

- 源码声明的类型、组件或调用边界：`SubagentActivityGroup`, `MemberTaskListItem`, `ProcessItem`, `ActivityIcon`, `toolName`, `activityLabel`, `labels`, `activityToolLabel`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { AlertCircle, CircleEllipsis, Lightbulb, ListTodo, Search, SquareTerminal, Wrench } from 'lu`；`import { memo, useMemo, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { LoadingSpinner } from '../ui/LoadingSpinner/LoadingSpinner';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/subagent/SubagentExpandedPanel.tsx#L1-L695)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/subagent/SubagentStatusIcon.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b3e0c84d5e6719eac1e189b8c2ef13582e0d30f44ec21aa7813c61ee2818fd88 -->
**`jiuwenswarm/channels/web/frontend/src/components/subagent/SubagentStatusIcon.tsx`**

- 源码声明的类型、组件或调用边界：`SubagentStatusIcon`, `tone`, `label`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import { CircleAlert } from 'lucide-react';`；`import { LoadingSpinner } from '../ui/LoadingSpinner/LoadingSpinner';`；`import SuccessIcon from '../../assets/subagent/success.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/subagent/SubagentStatusIcon.tsx#L1-L37)。
<!-- /kb:file -->
