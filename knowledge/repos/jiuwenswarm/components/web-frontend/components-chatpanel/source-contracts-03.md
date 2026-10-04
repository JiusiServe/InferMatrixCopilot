---
title: "components-chatpanel 源码接口与集成边界 03"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-chatpanel 源码接口与集成边界 03

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/clipboardImagePaste.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=49dd956153c58278e854a323d5acc4dd1a50f2ab8fa452c2c465e14ee7e27605 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/clipboardImagePaste.ts`**

- 源码声明的类型、组件或调用边界：`ACCEPTED_IMAGE_TYPES`, `IMAGE_EXTENSIONS`, `IMAGE_INPUT_DISABLED_ALERT_KEY`, `ImageInputDisabledState`, `isImageInputDisabled`, `shouldAlertImagePasteDisabled`, `getFileExtension`, `idx`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/clipboardImagePaste.ts#L1-L158)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/evolution-status.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6dedfa54853976853424cb5a81e13474306ede7a32c39b96234bc7c5a7b8aaa6 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/evolution-status.ts`**

- 源码声明的类型、组件或调用边界：`Translate`, `STAGE_KEY_MAP`, `getEvolutionPillLabel`, `stage`, `translationKey`, `message`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AgentMode } from '../../types/index.ts';`；`import type { EvolutionStatusPayload } from '../../types/websocket.ts';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/evolution-status.ts#L1-L46)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c3c5069276c4f30acd69953c3e0d8e94a594456357c5c81626d9994a8b844f96 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/index.tsx`**

- 源码声明的类型、组件或调用边界：`ChatSendOptions`, `MessageForkPoint`, `Permission`, `ProjectInfo`, `InputAreaHandle`, `TeamMemberIdentity`, `DesktopLocalFilesEventDetail`, `LocalFilePick`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import React, { useRef, useEffect, useLayoutEffect, useCallback, useMemo, useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import {`；`import type { TFunction } from 'i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/index.tsx#L1-L2138)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/projectSelection.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0cdd17265e96760819413ef5ab677c64f88824a11dcd58402dca40b40c79b2a5 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/projectSelection.ts`**

- 源码声明的类型、组件或调用边界：`isDefaultInputProject`, `getInputProjectOptions`, `keyword`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ProjectInfo } from '../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/projectSelection.ts#L1-L14)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/slashCommands/registry.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=51634e9bf1a3f8ca3e30c1a4e55102010be52086f60823b06a59ad97b92ce0a8 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/slashCommands/registry.ts`**

- 源码声明的类型、组件或调用边界：`SlashCommandContext`, `SlashCommand`, `PlanSlashStore`, `GoalSlashStore`, `GoalPlanSlashStore`, `GoalSlashAction`, `GoalSlashSnapshot`, `GoalSlashIntent`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { webRequest } from '../../../services/webClient';`；`import type { Message } from '../../../types/message';`；`import { useGoalStore } from '../../../stores/goalStore';`；`import { usePlanStore } from '../../../stores/planStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/slashCommands/registry.ts#L1-L420)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/slashCommands/semantics.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c264ba9d67e9d3d031de977088f894b72f5fac694ce52e0e6c89c0973cb499c1 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/slashCommands/semantics.ts`**

- 源码声明的类型、组件或调用边界：`supportsWebSlashCommands`, `getWebSlashCommandsForMode`, `resolveSlashCommandDescription`, `locale`, `descriptions`, `GoalWithStatus`, `hasUnfinishedGoal`, `PlanGoalInterlockDecision`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/slashCommands/semantics.ts#L1-L56)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/teamEventUtils.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f551f2e7a2129b3b3cf3b8990671c6d5e3fb2d9aed5ca1db8033efade2e1bf97 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/teamEventUtils.ts`**

- 源码声明的类型、组件或调用边界：`ParsedTeamEvent`, `formatTeamEventTime`, `date`, `parseTeamEventMessage`, `jsonStr`, `payload`, `event`, `type`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Message } from '../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/teamEventUtils.ts#L1-L78)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/timelineRowState.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0976e3d9ea358a586d42d8ad2a1bf62883b42a29a9b87a438975bd38c0f010de -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/timelineRowState.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `TimelineRowStateContext`, `TimelineRowStateProvider`, `context`, `useTimelineRowState`, `context`, `key`, `updateValue`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createContext, useCallback, useContext, useMemo, useState, type ReactNode, type SetStateAct`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/timelineRowState.tsx#L1-L37)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/toolCategory.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=18f43d83a6448e185e56b747925da2217dcf389f94d24a88fe97c0daa0e88ef9 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/toolCategory.ts`**

- 源码声明的类型、组件或调用边界：`ToolCategory`, `TOOL_CATEGORY_ORDER`, `ToolDisplayDefinition`, `normalize`, `TOOL_DISPLAY_REGISTRY`, `register`, `name`, `humanizeToolName`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/toolCategory.ts#L1-L183)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/unsentImageDiscard.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=02eecf574fe7cd3b35de8101e889b25e79d1ab7f93afcafdd43099d08cfa5748 -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/unsentImageDiscard.ts`**

- 源码声明的类型、组件或调用边界：`UnsentImageDraft`, `UnsentImageDiscardPlan`, `planUnsentImageDiscard`, `keptPaths`, `draft`, `pendingIds`, `paths`, `seenPaths`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/unsentImageDiscard.ts#L1-L37)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ChatPanel/useProcessTreeCollapse.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8bed33ced4766bfd49d21430e92e76b5084a172084b563be72c982d08a84770f -->
**`jiuwenswarm/channels/web/frontend/src/components/ChatPanel/useProcessTreeCollapse.ts`**

- 源码声明的类型、组件或调用边界：`SetStateAction`, `useProcessTreeCollapse`, `setCollapsed`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, type SetStateAction } from 'react';`；`import { useTimelineRowState } from './timelineRowState';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ChatPanel/useProcessTreeCollapse.ts#L1-L23)。
<!-- /kb:file -->
