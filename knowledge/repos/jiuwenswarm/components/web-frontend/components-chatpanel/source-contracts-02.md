---
title: "components-chatpanel 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-chatpanel 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/PermissionWarningDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=db373096aa99b7c098d8d42b616639109f24f8ddecc6618734a551836c2a7d7a -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/PermissionWarningDialog.tsx`**

- 源码声明的类型、组件或调用边界：`PermissionWarningDialogProps`, `PermissionWarningDialog`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/PermissionWarningDialog.tsx#L1-L74)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/PickerPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7fa295fe92f03d3f7b401810b05636208475a05089e011d754de73510d4c07aa -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/PickerPanel.tsx`**

- 源码声明的类型、组件或调用边界：`DEFAULT_MAX_VISIBLE_ROWS`, `DEFAULT_ROW_GAP`, `VIEWPORT_BOTTOM_GAP`, `VIEWPORT_TOP_GAP`, `listContentHeight`, `PickerPanelProps`, `PickerPanel`, `contentHeight`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import type { CSSProperties, MouseEventHandler, MutableRefObject, ReactNode, RefObject } from 'react`；`import clsx from 'clsx';`；`import MoreIcon from '../../assets/agent-management/more.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/PickerPanel.tsx#L1-L181)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/PickerSearchInput.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=72298b871ba6df365c5cfb4c9e4b09c9bc05d4016ab063c9c4dece97d7766adc -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/PickerSearchInput.tsx`**

- 源码声明的类型、组件或调用边界：`PickerSearchInputProps`, `PickerSearchInput`, `showClear`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import SearchIcon from '../../assets/agent-management/agent-search.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/PickerSearchInput.tsx#L1-L47)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ProactiveRecommendationCard.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3712d58e591f726bf91f2b7dd2c2dc50ffe074c2e521402a4e0b1d4764d06ed4 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ProactiveRecommendationCard.tsx`**

- 源码声明的类型、组件或调用边界：`ProactiveRecommendationCardProps`, `FEEDBACK_LS_PREFIX`, `loadFeedbackGiven`, `v`, `saveFeedbackGiven`, `typeConfig`, `ProactiveRecommendationCard`, `proactiveType`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import React, { useState, useCallback } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Sparkles, Clock, Compass, ThumbsUp, ThumbsDown } from 'lucide-react';`；`import ReactMarkdown from 'react-markdown';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ProactiveRecommendationCard.tsx#L1-L172)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/SkillPickerPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2e8f18ba27374ca68ec2ab7f9d39a9b9a0bebe598e48d054e24cd9a5ee3ea3da -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/SkillPickerPanel.tsx`**

- 源码声明的类型、组件或调用边界：`RefObject`, `SkillItem`, `SkillType`, `InstalledPlugin`, `LIST_ROW_HEIGHT`, `SkillPickerPanelProps`, `SkillPickerPanel`, `activeSessionId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import clsx from 'clsx';`；`import { useChatStore, useSessionStore } from '../../stores';`；`import { webRequest } from '../../services/webClient';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/SkillPickerPanel.tsx#L1-L265)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/SkillTreePath.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=28440cf4df5967428ebed3b8b909911a2c97ab43575c8d676fa76a8b059b6d69 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/SkillTreePath.tsx`**

- 源码声明的类型、组件或调用边界：`SkillTreePathProps`, `BrowseNodeKind`, `BrowseNode`, `BrowseGraph`, `MAX_VISIBLE_CHILDREN`, `collectTrees`, `result`, `normalizeId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useMemo, useRef, useState } from 'react';`；`import clsx from 'clsx';`；`import type {`；`import './SkillTreePath.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/SkillTreePath.tsx#L1-L569)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/StreamingContent.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=58a5f5fb0af98e59af9e2160edc6bca4d772c00a397a9e76e1fe4c2f5a442abb -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/StreamingContent.tsx`**

- 源码声明的类型、组件或调用边界：`StreamingContentProps`, `StreamingContent`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/StreamingContent.tsx#L1-L11)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/TeamEventGroupDisplay.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=77f26aab567178df54813257b0f2e12e5047fc5e4352fee613633d46db5cb694 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/TeamEventGroupDisplay.tsx`**

- 源码声明的类型、组件或调用边界：`TodoItem`, `ParsedTeamEvent`, `ActivityStatus`, `Translate`, `AgentTeamActivityCardProps`, `TeamMemberLike`, `MemberActivity`, `ActivityCandidate`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { ListChecks, MessageSquareText, Wrench } from 'lucide-react';`；`import { Message, type TodoItem } from '../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/TeamEventGroupDisplay.tsx#L1-L589)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ToolCallDisplay.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f0a9b248033ac47f619c1da319e4d3c483ab11bfcc732ffa59089dec922dc737 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ToolCallDisplay.tsx`**

- 源码声明的类型、组件或调用边界：`ToolCallDisplayProps`, `DisclosureChevron`, `ToolCallDisplay`, `isSession`, `displayTitle`, `callGoal`, `displaySubtitle`, `isSymphonyCommand`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { ToolCall, ToolResult } from '../../types';`；`import { formatToolArguments, formatToolResult } from '../../utils';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ToolCallDisplay.tsx#L1-L170)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ToolGroupDisplay.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0d9d82da3f233a2d43e201adf451467c0e70a35c2d11b1255f4f1040c97b5cec -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ToolGroupDisplay.tsx`**

- 源码声明的类型、组件或调用边界：`ToolCategory`, `TeamLeaderIdentity`, `ToolGroupDisplayProps`, `ToolStatusTone`, `TOOL_FLOWCHART_CANVAS_MIN_HEIGHT`, `ToolStatusIcon`, `isToolResultSuccessful`, `isToolExecutionFailed`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback } from 'react';`；`import { useTimelineRowState } from './timelineRowState';`；`import { useTranslation } from 'react-i18next';`；`import clsx from 'clsx';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ToolGroupDisplay.tsx#L1-L553)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/VirtualTimeline.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b8716d3c427fa5d40d506c309ecb839f5dece90fd7baa2c5f3198e3d2e5f984b -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/VirtualTimeline.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `VirtualItem`, `ROW_GAP`, `ESTIMATED_ROW_HEIGHT`, `TimelineViewportState`, `VirtualTimelineProps`, `VirtualTimeline`, `containerRef`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useLayoutEffect, useRef, useState, type ReactNode } from 'react';`；`import { useVirtualizer, type VirtualItem } from '@tanstack/react-virtual';`；`import type { TimelineDisplayItem } from '../../features/chatTimeline/projectTimelineItems';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/VirtualTimeline.tsx#L1-L150)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/beamSearchTreeModel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f5e64bd59101905ef95813c3d9bafc26eccc6acfffc88fd14d75104372ee7cc5 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/beamSearchTreeModel.ts`**

- 源码声明的类型、组件或调用边界：`BeamTreeNodeEntry`, `BeamTreeMergeEntry`, `BeamTreeEntry`, `BeamTreeModel`, `compareNodes`, `compareEdges`, `leftNode`, `rightNode`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/beamSearchTreeModel.ts#L1-L114)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/chatTimelineClock.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=391b06cf44b814e799988d4ad721d346ac218665562ec22485b29eec7d1431a0 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/chatTimelineClock.ts`**

- 源码声明的类型、组件或调用边界：`formatDurationPrecise`, `clamped`, `totalSeconds`, `totalMinutes`, `seconds`, `hours`, `minutes`, `useNow`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/chatTimelineClock.ts#L1-L34)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/imeComposition.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=36e8b4d63744b5da6afab7628552b1523b7c0308263bcaed0c82676355ddbd33 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/imeComposition.ts`**

- 源码声明的类型、组件或调用边界：`ImeKeyboardEvent`, `isImeCompositionKey`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/imeComposition.ts#L1-L13)。
<!-- /kb:file -->
