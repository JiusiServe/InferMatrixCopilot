---
title: "features-rsi 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-rsi 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1315c8342f80fcd1e5a273249b9fecaa9cf19566f6aef4431624a37958eea715 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx`**

- 源码声明的类型、组件或调用边界：`RsiPage`, `list`, `listLoading`, `listError`, `selectedTaskId`, `loadList`, `selectTask`, `upsertListItem`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { useRsiStore } from './rsiStore';`；`import { useRsiEvents } from './useRsiEvents';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/RsiPage.tsx#L1-L88)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e72dcab923ec791d823eccebfde1326c1560a38d1abf54ceb2c0a09fca37e65b -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx`**

- 源码声明的类型、组件或调用边界：`ConfigInfoDialogProps`, `ConfigInfoDialog`, `ref`, `dialog`, `cfg`, `isArtifact`, `isPaper`, `isProgram`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useRef } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import type { RsiTaskGetResult } from '../types';`；`import { scenarioLabel, artifactTypeLabel } from '../rsiPresentation';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/ConfigInfoDialog.tsx#L1-L95)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ca7a5805f5644e41f5d8ae0043662603251f93b2c67b74539267682294b52d67 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx`**

- 源码声明的类型、组件或调用边界：`RSI_DATASET_FIELD_SCHEMA`, `DatasetFieldTipContent`, `handleCopy`, `CreateExperimentDialogProps`, `Branch`, `DEFAULT_RSI_PACKAGE_ID`, `FormState`, `defaultForm`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import clsx from 'clsx';`；`import { Check, Copy } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/CreateExperimentDialog.tsx#L1-L1004)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiArtifactDetailDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1034e32147bab01b959410ea2e75f251d325543311102a41615b35229a4f2d9d -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiArtifactDetailDialog.tsx`**

- 源码声明的类型、组件或调用边界：`RsiArtifactFileEntry`, `RsiArtifactSource`, `RsiArtifactDetailDialogProps`, `FileTreeNode`, `createFileTree`, `root`, `directoryMap`, `entry`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useState } from 'react';`；`import { ChevronRight, Copy, Download, File as FileIcon, Folder, LoaderCircle, X } from 'lucide-reac`；`import { useTranslation } from 'react-i18next';`；`import { FilePreview } from '../../../components/ArtifactsPanel/FilePreview';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiArtifactDetailDialog.tsx#L1-L383)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiCanvasArea.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=85d3a5260004623f2c7f3765e4ac0f6b7431ddc41ae68ae63231865479e2209b -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiCanvasArea.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `StatusBadgeKind`, `NodeStatusKind`, `NodeIconKind`, `RsiNodePresentation`, `LayoutNode`, `RsiCanvasAreaProps`, `LEGEND`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { memo, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import bestIcon from '../../../assets/rsi/rsi-best.svg';`；`import costIcon from '../../../assets/rsi/rsi-cost.svg';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiCanvasArea.tsx#L1-L1013)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiDetail.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f5c80f5d9f51850a3a32b2cd5c9b983d8fb3b8e7717130bb7ffc4f2f5cea91d5 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiDetail.tsx`**

- 源码声明的类型、组件或调用边界：`RsiDetail`, `selectedTaskId`, `detail`, `detailLoading`, `refreshDetail`, `list`, `status`, `cancelled`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { useRsiStore } from '../rsiStore';`；`import { RsiDetailHeader } from './RsiDetailHeader';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiDetail.tsx#L1-L94)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiDetailHeader.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=50318773ba529347614310856d7fa9f6e5965d7f13ae0dcab723202500cb539a -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiDetailHeader.tsx`**

- 源码声明的类型、组件或调用边界：`DesktopSaveApiResult`, `StatusBadgeKind`, `RsiActionKind`, `DownloadCapableWindow`, `RsiDetailHeaderProps`, `RsiDetailHeader`, `patchTaskStatus`, `removeListItem`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { executeDesktopSave, type DesktopSaveApiResult } from '../../../utils/desktopSave';`；`import completeIcon from '../../../assets/rsi/rsi-complete.svg';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiDetailHeader.tsx#L1-L439)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiIntroduction.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0e9fecfda7bf07914ad079184103a88cbfb32c93d239dee77b6f8f61c86d3ad2 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiIntroduction.tsx`**

- 源码声明的类型、组件或调用边界：`RsiIntroductionProps`, `DESIGN_WIDTH`, `MAX_SCALE`, `RsiIntroduction`, `scalerRef`, `contentRef`, `scaler`, `content`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useLayoutEffect, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import step1Image from '../../../assets/rsi/rsi-step1.svg';`；`import step2Image from '../../../assets/rsi/rsi-step2.svg';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiIntroduction.tsx#L1-L130)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiLatexPreview.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b16dd0991ace4f015d3f2b3f24ad720357378637732a406119bfe08e11eb7222 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiLatexPreview.tsx`**

- 源码声明的类型、组件或调用边界：`RsiLatexPreviewProps`, `LatexViewMode`, `RsiLatexPreview`, `cancelled`, `text`, `markdown`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useMemo, useState } from 'react';`；`import { LoaderCircle } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import { MarkdownRenderer } from '../../../components/MarkdownRenderer';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiLatexPreview.tsx#L1-L88)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiRail.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=257a09a03e553ba094632742f949801645108d825bb77b9e32b0408bc87e9102 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiRail.tsx`**

- 源码声明的类型、组件或调用边界：`RsiRailProps`, `RsiRail`, `active`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import type { RsiTaskListItem } from '../types';`；`import { statusBadgeInfo, typeDisplayLabel } from '../rsiPresentation';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiRail.tsx#L1-L76)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiResultSummary.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3509e6f8ebc117df99ce714c45c8a606c5ddae71b4bba189c1d9dd8dcb93a8c6 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiResultSummary.tsx`**

- 源码声明的类型、组件或调用边界：`RsiResultSummaryProps`, `RsiResultSummary`, `liveProgress`, `tree`, `score`, `baseline`, `gain`, `gainFmt`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import optimizeImage from '../../../assets/rsi/rsi-optimize.svg';`；`import type { RsiTaskGetResult, RsiReportGetResult, RsiUsageGetResult } from '../types';`；`import { formatArtifactScore, formatGain, formatTokensK, presentRsiNode, typeDisplayLabel } from '..`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiResultSummary.tsx#L1-L138)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiSelectedInfo.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=299cb560cb1dfeb917de71b5679ab7f55f7512358d1629c33e8e4e35131ce048 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiSelectedInfo.tsx`**

- 源码声明的类型、组件或调用边界：`HARNESS_GROUPS`, `RsiSelectedInfoProps`, `RsiSelectedInfo`, `tree`, `task`, `selectedNodeId`, `setSelectedNode`, `selected`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import selectedInfoIcon from '../../../assets/rsi/rsi-icon.svg';`；`import { useRsiStore } from '../rsiStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/components/RsiSelectedInfo.tsx#L1-L232)。
<!-- /kb:file -->
