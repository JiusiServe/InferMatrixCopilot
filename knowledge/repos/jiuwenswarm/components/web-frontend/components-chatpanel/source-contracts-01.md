---
title: "components-chatpanel 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-chatpanel 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/AutoReviewerStatus.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=118432120b3233aa581758e011b79e4a68bde3f6bf34e588a2521ee0ca57f34f -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/AutoReviewerStatus.tsx`**

- 源码声明的类型、组件或调用边界：`AutoReviewerBadgeTone`, `BADGE_TONE_CLASS`, `MANUAL_DECISION_SOURCES`, `FAILURE_STATUSES`, `MANUAL_ACTION_STATUSES`, `RISK_LEVELS`, `ReviewerDecisionSourceCategory`, `reviewerDecisionSourceCategory`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import clsx from 'clsx';`；`import { useTranslation } from 'react-i18next';`；`import type { AutoReviewerMetadata, AutoReviewerStatus } from '../../types';`；`import { effectiveReviewerStatus, normalizeReviewerStatus } from '../../features/tool-events/reviewe`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/AutoReviewerStatus.tsx#L1-L157)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/BeamSearchTree.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=28e649e9507991055c25f125e1bcdecde383e88764a93171afcaaf0e870017d2 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/BeamSearchTree.tsx`**

- 源码声明的类型、组件或调用边界：`BeamTreeMergeEntry`, `BeamTreeNodeEntry`, `MAX_VISIBLE_REJECTED_CHILDREN`, `BeamTreeCopy`, `COPY`, `BeamMergeReference`, `label`, `BeamTreeNodeCard`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo } from 'react';`；`import { useTimelineRowState } from './timelineRowState';`；`import clsx from 'clsx';`；`import { ChevronDown, GitMerge } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/BeamSearchTree.tsx#L1-L232)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ChatModelSelector.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2b90da2df6a3dadad44da818b37a6829073d0e7dbaca7e1623039ba8142b7eb0 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ChatModelSelector.tsx`**

- 源码声明的类型、组件或调用边界：`openModelSettings`, `ChatModelSelector`, `models`, `activeSessionId`, `selectedModelName`, `defaultModelName`, `setSelectedModelName`, `selected`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { requestSettingsModule } from '../../features/settings/settingsNavigation';`；`import { useChatStore } from '../../stores/chatStore';`；`import { resolveChatModelSelection, useSessionStore } from '../../stores/sessionStore';`；`import ModelPicker from '../ModelPicker';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ChatModelSelector.tsx#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d652290ac4d83efcef80cb57cdd634f6756d770bd503656b659cb3618bd48930 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx`**

- 源码声明的类型、组件或调用边界：`CSSProperties`, `VIEWPORT_GAP`, `TOOLTIP_GAP`, `TOOLTIP_ALIGN_OFFSET`, `DETAIL_GAP`, `useElementWidth`, `element`, `updateWidth`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type RefObje`；`import { createPortal } from 'react-dom';`；`import { X } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ContextUsageIndicator.tsx#L1-L318)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ExtensionPickerPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f4cd229411cf1ee0d1386cf0fd9f33eb42e9aef4bb7990ee9cd9b2bfdbe3c357 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ExtensionPickerPanel.tsx`**

- 源码声明的类型、组件或调用边界：`RefObject`, `LIST_ROW_HEIGHT`, `ExtensionPickerPanelProps`, `ExtensionPickerPanel`, `activeSessionId`, `enabledPlugins`, `enabledMcps`, `packages`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useMemo, useRef, useState, type RefObject } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Loader2 } from 'lucide-react';`；`import { useChatStore, useSessionStore } from '../../stores';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/ExtensionPickerPanel.tsx#L1-L458)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/FileDownloadMediaPreviewContext.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=db2626e64c988798c66e9a18cada73e180f0c69e5029e06efeff9d9b562423d0 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/FileDownloadMediaPreviewContext.ts`**

- 源码声明的类型、组件或调用边界：`FileDownloadMediaPreviewContext`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createContext } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/FileDownloadMediaPreviewContext.ts#L1-L4)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/HarnessProgressBar.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f61cd763cd445b7363367d260aa8c8f59fc77c83f15a010a7f47adbc56550ad5 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/HarnessProgressBar.tsx`**

- 源码声明的类型、组件或调用边界：`StageStatusIconProps`, `StageStatusIcon`, `StageItemProps`, `StageItem`, `visibleMessages`, `normalized`, `hasDetails`, `ExtensionStatusIcon`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import React, { useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { useHarnessStore, useSessionStore, useChatStore } from '../../stores';`；`import type { ExtensionProgressInfo, ExtensionProgressStatus } from '../../stores/harnessStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/HarnessProgressBar.tsx#L1-L431)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/InlineQuestionCard.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0e41c268aa5dc5f58f5cb137a56efeefbdbfd6116a7f2cb56c3ce8d5aad4b51e -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/InlineQuestionCard.tsx`**

- 源码声明的类型、组件或调用边界：`InlineQuestionCardProps`, `OTHER_VALUE`, `isOtherOption`, `ApprovalQuestionContent`, `PlanApprovalActions`, `hasRevision`, `InlineQuestionCard`, `activeSessionId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState, useCallback, useMemo, useEffect } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { useChatStore } from '../../stores';`；`import { UserAnswer, QuestionOption, Question } from '../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/InlineQuestionCard.tsx#L1-L587)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/InputArea.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f77218976c91ca73f98882c8ce206e7c8188e06cabfcc2b1644ec76ddcb0fcfc -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/InputArea.tsx`**

- 源码声明的类型、组件或调用边界：`CSSProperties`, `RefObject`, `SVGProps`, `ProjectInfo`, `ProjectCreateMode`, `GoalSlashAction`, `GoalSlashSnapshot`, `SlashCommand`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`；`import type { TFunction } from 'i18next';`；`import { AtSign, ChevronRight, CircleX, Loader2, Lock, Mic, Plus, Settings, Square, Workflow, X } fr`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/InputArea.tsx#L1-L5372)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MediaRenderer.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=608b2badec254f48a9c1d476cabc6a4460a148cbd560f8161e6df2c85440694c -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MediaRenderer.tsx`**

- 源码声明的类型、组件或调用边界：`MediaRendererProps`, `VISIBLE_FILE_COUNT`, `isImageItem`, `isCardItem`, `mediaSrc`, `mimeType`, `base64Data`, `FileCard`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useRef, useState } from 'react';`；`import { MediaItem } from '../../types';`；`import { FileIcon, getFileExtensionLabel } from '../FileIcon';`；`import { stripUploadDocumentBlocks } from '../../utils/documentMessage';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MediaRenderer.tsx#L1-L239)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MessageItem.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9c27ec37d728bf1987a1e14d5a5a75312b08f9de6853fd665d861b0788a54e85 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MessageItem.tsx`**

- 源码声明的类型、组件或调用边界：`DesktopSaveApiResult`, `TeamLeaderIdentity`, `openArtifactPanelForActiveMode`, `sessionId`, `mode`, `MarkdownMessageBody`, `CompactCommandDivider`, `TeamMemberMessageFrame`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState, useCallback, useContext, useEffect, useRef, useMemo, memo } from 'react';`；`import type { ReactNode } from 'react';`；`import {`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MessageItem.tsx#L1-L1280)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MessageList.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9c4c4379878bff60186ad8d17d0966299c8425ce95d1db193c562d598634112b -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MessageList.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `TimelineDisplayItem`, `TimelineViewportState`, `LiveWorkStreak`, `EMPTY_EXPANSIONS`, `EMPTY_REASONING`, `MessageListProps`, `ChatTimelineListProps`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Fragment, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';`；`import clsx from 'clsx';`；`import { LoaderCircle } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/MessageList.tsx#L1-L944)。
<!-- /kb:file -->
