---
title: "features-trajectory 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-trajectory 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/SingleAgentSurface.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c8f57bdd7a6fd4bfd41d9b683290277957f4459e93bac0e5b43272232e1c24dd -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/SingleAgentSurface.tsx`**

- 源码声明的类型、组件或调用边界：`ChatSurfaceView`, `SingleAgentSurfaceProps`, `SingleAgentSurface`, `trajectoryMode`, `navigationVisible`, `resolvedView`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/SingleAgentSurface.tsx#L1-L99)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/TeamTrajectoryWorkspace.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aa3e60eeed55cc1fb93a7ff9285d6fbd699a4b30ff2d6c27fcf97beadb50b2fc -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/TeamTrajectoryWorkspace.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `TrajectoryKey`, `TeamMemberLaneModel`, `TeamMemberViewContext`, `TeamTrajectoryWorkspaceProps`, `MemberToolbarControl`, `TeamTrajectoryWorkspace`, `lanes`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { memo, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import type { TrajectoryViewState } from './client/TrajectoryExplorer';`；`import { trajectoryTranslator, type TrajectoryKey } from './client/i18n';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/TeamTrajectoryWorkspace.tsx#L1-L169)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/TrajectoryPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=adae9deb14d449bbcbfa5970f7ddb09dd6143dc8df777f76ff4007f8e0354a3d -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/TrajectoryPanel.tsx`**

- 源码声明的类型、组件或调用边界：`ChangeEvent`, `KeyboardEvent`, `PointerEvent`, `TrajectoryRetentionCheckpoints`, `TrajectoryDetailRecord`, `TrajectorySubjectSummary`, `TrajectoryArchiveProgress`, `TrajectoryArchiveReplay`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import { useTranslation } from 'react-i18next';`；`import { webClient } from '../../services/webClient';`；`import { saveBlobWithResult } from '../../utils/desktopSave';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/TrajectoryPanel.tsx#L1-L1771)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/client/TrajectoryExplorer.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f67b765c9b372def6451878893fc0696b3de3c4cea9f6dac1455085db7de5f59 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/client/TrajectoryExplorer.tsx`**

- 源码声明的类型、组件或调用边界：`CSSProperties`, `TrajectoryTimelineMode`, `TrajectoryTimeRange`, `TrajectoryColorMode`, `TrajectoryKey`, `EMPTY_TURN_IDS`, `EMPTY_RECORD_IDS`, `ExplorerStyle`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import type {`；`import { trajectoryRecordId } from '../trajectory/record.ts'`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/client/TrajectoryExplorer.tsx#L1-L365)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/client/TrajectoryTable.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=216a0055a2c795b8845a9f008633d979c602762f387772977c2b9a8dc7fa482b -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/client/TrajectoryTable.tsx`**

- 源码声明的类型、组件或调用边界：`BOTTOM_FOLLOW_THRESHOLD_PX`, `VIRTUALIZATION_THRESHOLD`, `VIRTUAL_OVERSCAN_ROWS`, `VIRTUAL_INITIAL_VIEWPORT_HEIGHT_PX`, `KIND_LABEL`, `ToolWrenchIcon`, `InformationIcon`, `CompactedIcon`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'`；`import type { CSSProperties, ReactNode } from 'react'`；`import { useVirtualizer } from '@tanstack/react-virtual'`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/client/TrajectoryTable.tsx#L1-L3342)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/client/TrajectoryTimeline.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e1cb864d6a83d3b0f04120f8cb4820f6c956c21dd7c92cd5337c707f89f9f3a6 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/client/TrajectoryTimeline.tsx`**

- 源码声明的类型、组件或调用边界：`CSSProperties`, `KeyboardEvent`, `TrajectoryTimelineMode`, `TrajectoryTimelineSegment`, `TrajectoryTimelineSpan`, `TrajectoryTimeRange`, `MINIMUM_DRAG_PX`, `MINIMUM_ZOOM_OPERATIONS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import { Tooltip } from '../primitives/index.ts'`；`import type { TrajectoryTurnModel } from '../trajectory/model.ts'`；`import type { AssistantMetricDetail, TrajectoryCellKind, TrajectoryCellProps } from '../trajectory/r`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/client/TrajectoryTimeline.tsx#L1-L934)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/client/TrajectoryToolbar.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=84fb75ee55aa1bf903827fc67854feb5eb6397ca1627ebb2c2c8e25adeb3c384 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/client/TrajectoryToolbar.tsx`**

- 源码声明的类型、组件或调用边界：`TrajectoryToolbarProps`, `TrajectoryToolbar`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react'`；`import { IconSearchOutline16 } from '../primitives/index.ts'`；`import type { TrajectoryTranslate } from './i18n.ts'`；`import css from './TrajectoryToolbar.module.css'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/client/TrajectoryToolbar.tsx#L1-L170)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/client/i18n.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0280979db019d729ca9e4a098cb3d892b04be35e75da0ff6086270dfcba192a0 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/client/i18n.ts`**

- 源码声明的类型、组件或调用边界：`TrajectoryKey`, `TrajectoryTranslate`, `en`, `trajectoryTranslator`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/client/i18n.ts#L1-L47)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/featureConfig.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=08d070ad5f70cb576bba6721d572f753e488d9a69c1478325af733438130e178 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/featureConfig.ts`**

- 源码声明的类型、组件或调用边界：`trajectoryUiEnabled`, `listeners`, `normalizeTrajectoryUiEnabled`, `setTrajectoryUiEnabled`, `isTrajectoryUiEnabled`, `subscribe`, `useTrajectoryUiEnabled`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useSyncExternalStore } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/featureConfig.ts#L1-L36)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/index.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4e24ba0e41365a77e4aa027a6512516b52f995152b8b0d259a512d96e1f7aa84 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/index.ts`**

- 集成边界的导入/加载声明：`import './client/theme.css'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/index.ts#L1-L72)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/JsonTree.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=639273b02996d89fe3e586a203e4e1881ef7cb8ccfbf21f7f1bf9b22ed3518c5 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/JsonTree.tsx`**

- 源码声明的类型、组件或调用边界：`OBJECT_PREVIEW_LIMIT`, `ARRAY_PREVIEW_LIMIT`, `PREVIEW_DEPTH_LIMIT`, `JsonTreeLabels`, `DEFAULT_LABELS`, `valueCopyMenuItems`, `objectCopyMenuItems`, `JsonPath`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import clsx from 'clsx'`；`import { useEffect, useId, useMemo, useRef, useState } from 'react'`；`import type {`；`import { IconCheckOutline16, IconCopyOutline16 } from './icons/index.tsx'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/JsonTree.tsx#L1-L664)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/Menu.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d0b67b70c30ba6dec94996c5539cd5c752b9086d28b2cb69b0c8111ab68c306d -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/Menu.tsx`**

- 源码声明的类型、组件或调用边界：`MenuItem`, `MenuSeparator`, `MenuLabel`, `MenuEntry`, `isSeparator`, `isLabel`, `MEASURE_STYLE`, `Menu`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useLayoutEffect, useRef, useState } from 'react'`；`import type { CSSProperties, ReactNode } from 'react'`；`import { createPortal } from 'react-dom'`；`import clsx from 'clsx'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/Menu.tsx#L1-L307)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/Tooltip.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0e28c03e487305515cf0ece86e8d4c3bbfd129362e0094cca4d7119f4ec7b768 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/Tooltip.tsx`**

- 源码声明的类型、组件或调用边界：`TooltipSide`, `AnchorProps`, `TooltipLabel`, `Tooltip`, `colorMode`, `anchor`, `childRef`, `mergedRef`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { cloneElement, useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'`；`import type { FocusEventHandler, MouseEventHandler, MutableRefObject, ReactElement, Ref } from 'reac`；`import { createPortal } from 'react-dom'`；`import { useTrajectoryColorMode } from '../theme/context.tsx'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/Tooltip.tsx#L1-L174)。
<!-- /kb:file -->
