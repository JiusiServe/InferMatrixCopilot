---
title: "components-teamarea 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-teamarea 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/AgentDetailModal.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8076db131b8f021a0bf40d36910aa03db3e1c55edd8c74f440290eab7054f6ac -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/AgentDetailModal.tsx`**

- 源码声明的类型、组件或调用边界：`formatCharCount`, `n`, `DetailSectionKey`, `DetailAccent`, `DetailSection`, `AgentModalState`, `accentTextClass`, `accentChipClass`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { MarkdownRenderer } from '../MarkdownRenderer';`；`import type { WorkflowAgent } from './workflowTypes';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/AgentDetailModal.tsx#L1-L379)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/CompactTaskList.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2e31d6c2c3e05a8b961a31db71ce98a832d0e12e1af8099105d8f244cfc56a27 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/CompactTaskList.tsx`**

- 源码声明的类型、组件或调用边界：`TaskColumnKey`, `compactStatusIcons`, `CompactTaskListProps`, `CompactTaskList`, `visibleTasks`, `assigneeExists`, `assigneeName`, `title`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { CircleAlert } from 'lucide-react';`；`import { ApplicationTaskControls } from '../../applicationPlugins/ApplicationTaskControls';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/CompactTaskList.tsx#L1-L154)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/ExpandedPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f2631c12fea672de0d86c9f24bba09cc4193f441f562842af62dff6fa23c1781 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/ExpandedPanel.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `ExpandedPanelProps`, `ExpandedPanel`, `tabPanelId`, `artifactsCount`, `handleToggleFullscreen`, `resolvedTab`, `tabs`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useId, type ReactNode } from 'react';`；`import { useFullscreenPanel } from '../../hooks';`；`import { useSessionArtifactsCount } from '../ArtifactsPanel';`；`import { ArtifactExpandedPanel } from '../ArtifactsPanel';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/ExpandedPanel.tsx#L1-L121)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/ExpandedPanelTabs.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5a52edbcc193fd494508e2d44fa71becc806add619818eb9f8b4404e5f9acf28 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/ExpandedPanelTabs.tsx`**

- 源码声明的类型、组件或调用边界：`KeyboardEvent`, `PanelTabItem`, `useExpandedPanelTabs`, `ExpandedPanelTabs`, `tabPanelId`, `handleTabCloseKeyDown`, `isActive`, `countSuffix`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useId, type KeyboardEvent, type ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Globe2, Minimize2 } from 'lucide-react';`；`import MaximizeIcon from '../../assets/maximize.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/ExpandedPanelTabs.tsx#L1-L185)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/MemberListItem.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d18181476d3441ffd9f8ec5f472bd71415e9e2a5ccbb47e82465f880a3fff0a6 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/MemberListItem.tsx`**

- 源码声明的类型、组件或调用边界：`TeamMember`, `TaskProgress`, `MemberListItem`, `displayName`, `statusKey`, `progressPercent`, `radius`, `strokeWidth`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { TeamMemberAvatar } from '../TeamMemberAvatar';`；`import PendingIcon from '../../assets/pending.svg?react';`；`import { LoadingSpinner } from '../ui/LoadingSpinner/LoadingSpinner';`；`import { getMemberPlainName, getMemberStatusKey, type TeamMember } from './shared';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/MemberListItem.tsx#L1-L121)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/MemberOverviewCard.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=26962513375e7c13a98c8778f8a5d13b8ef481a0013d11b53156188c1ffbbf94 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/MemberOverviewCard.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `MemberOverviewCardProps`, `MemberOverviewCard`, `toggleItem`, `next`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState, type ReactNode } from 'react';`；`import { TeamMemberAvatar } from '../TeamMemberAvatar';`；`import { ProcessListCard } from './ProcessListCard';`；`import type { ProcessItem } from './shared';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/MemberOverviewCard.tsx#L1-L81)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/MemberTaskList.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5564bb6b1370a518f9906f512c046b2522b9c223d8dd2844b6b1b156def47501 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/MemberTaskList.tsx`**

- 源码声明的类型、组件或调用边界：`MemberTask`, `MemberTaskListItem`, `MemberTaskListBar`, `completedCount`, `latestTask`, `aTime`, `bTime`, `MemberTaskListPanel`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import React, { useRef } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { StatusIcon, type MemberTask, type TaskStatus } from './shared';`；`import { useAdaptiveTooltip } from '../../hooks/useAdaptiveTooltip';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/MemberTaskList.tsx#L1-L132)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/ProcessListCard.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7e9371132d7c96d105e62ded1a008de012aa3636469665fa0ac14db17bb77feb -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/ProcessListCard.tsx`**

- 源码声明的类型、组件或调用边界：`ProcessDetailRow`, `Translate`, `getProcessMessageType`, `getExecutionKindLabel`, `buildProcessDetailRows`, `rows`, `ProcessListCard`, `expanded`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { MessageSquare, Wrench } from 'lucide-react';`；`import { Chevron, StatusIcon, getTaskStatusLabel, type ProcessDetailRow, type ProcessItem, type Task`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/ProcessListCard.tsx#L1-L190)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/SwarmflowGraphView.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6b0dd589d669b10eb88dee7303e2cb472ffa9affce569a8d446cf7dfe4ee6449 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/SwarmflowGraphView.tsx`**

- 源码声明的类型、组件或调用边界：`Node`, `Edge`, `NodeProps`, `WorkflowRun`, `WorkflowPhase`, `WorkflowAgent`, `WorkflowStatus`, `WorkflowVerifyGroup`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useState } from 'react';`；`import {`；`import '@xyflow/react/dist/style.css';`；`import dagre from '@dagrejs/dagre';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/SwarmflowGraphView.tsx#L1-L922)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/SwarmflowTreeView.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=71fc4fcb176b448b83270336fb9e881e01cd26c1533c9ca7cc0efef4c1bc389d -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/SwarmflowTreeView.tsx`**

- 源码声明的类型、组件或调用边界：`ReactElement`, `WorkflowRun`, `WorkflowPhase`, `WorkflowAgent`, `WorkflowStatus`, `WorkflowVerifyGroup`, `AgentModalState`, `DetailSection`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useState, type ReactElement } from 'react';`；`import {`；`import { useTranslation } from 'react-i18next';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/SwarmflowTreeView.tsx#L1-L1686)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/TaskPlanningPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=25e348ca18a5a88e936123c1754e9d1ef67c3f2b00dfcbe394a10a468cafc548 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/TaskPlanningPanel.tsx`**

- 源码声明的类型、组件或调用边界：`TaskColumnKey`, `TeamMember`, `TaskPlanningPanelProps`, `COLUMN_STATS`, `ProgressBar`, `ProgressSection`, `emptyIllustrationSize`, `progressPercent`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo, useState } from 'react';`；`import type { ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { File, GitBranch, Maximize2, Puzzle } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/TaskPlanningPanel.tsx#L1-L701)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/teamArea/TeamMembersPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d4ee6b3e7fcbfea033f1890fda67f6ef6fae32b1b868e8e8fca17f068ec2abc1 -->
**`jiuwenswarm/channels/web/frontend/src/components/teamArea/TeamMembersPanel.tsx`**

- 源码声明的类型、组件或调用边界：`TeamConnectionPresentation`, `ParsedTeamEvent`, `TeamDetailTab`, `TeamMember`, `TeamMembersPanelProps`, `GroupMessageItem`, `getGroupMemberIds`, `isGroupMessageItem`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { memo, useEffect, useMemo, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { useChatStore, useSessionStore, useTodoStore } from '../../stores';`；`import type { Message, TeamMemberContextCompressionState } from '../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/teamArea/TeamMembersPanel.tsx#L1-L752)。
<!-- /kb:file -->
