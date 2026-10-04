---
title: "components-personalcontext 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-personalcontext 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/PersonalContext/AddContentDrawer.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=afef095e425ab72a3543baace93b546f4b6d5e7469e73c1019e3aae29588d5cd -->
**`jiuwenswarm/channels/web/frontend/src/components/PersonalContext/AddContentDrawer.tsx`**

- 源码声明的类型、组件或调用边界：`FetchProvider`, `FetchServiceConfig`, `FeishuMode`, `FeishuResource`, `GithubResource`, `GitcodeResource`, `TimeRange`, `PROVIDER_ICON`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useMemo, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { ChevronDown, Loader2, X } from 'lucide-react';`；`import { usePersonalContextStore } from '../../stores';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/PersonalContext/AddContentDrawer.tsx#L1-L1390)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/PersonalContext/GraphPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1038a8e12900f8a029f3c0f456a828416560e0e9757a68ba75e5707be454d20f -->
**`jiuwenswarm/channels/web/frontend/src/components/PersonalContext/GraphPanel.tsx`**

- 源码声明的类型、组件或调用边界：`LayoutEdge`, `LayoutNode`, `ContextEdge`, `ContextNode`, `ContextSearchResultItem`, `ContextSourceDetail`, `PersonalContextGraphPanelProps`, `Transform`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import { useTranslation } from 'react-i18next';`；`import { ChevronDown, Loader2, RefreshCw, Search, X } from 'lucide-react';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/PersonalContext/GraphPanel.tsx#L1-L1667)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/PersonalContext/Intro.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5e9ff387733e533938aa506b799f3220528075edf9428350389a94bced2a554e -->
**`jiuwenswarm/channels/web/frontend/src/components/PersonalContext/Intro.tsx`**

- 源码声明的类型、组件或调用边界：`INTRO_SEEN_KEY`, `isPersonalContextIntroSeen`, `PersonalContextIntroProps`, `PersonalContextIntro`, `handleStart`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import pcFeature1 from '../../assets/pc-feature-1.svg';`；`import pcFeature2 from '../../assets/pc-feature-2.svg';`；`import pcFeature3 from '../../assets/pc-feature-3.svg';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/PersonalContext/Intro.tsx#L1-L114)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/PersonalContext/ServicesPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ea415436d744dc6298cc2432a555ce56c7ca7d1f6daaeae2c3f26672f481342b -->
**`jiuwenswarm/channels/web/frontend/src/components/PersonalContext/ServicesPanel.tsx`**

- 源码声明的类型、组件或调用边界：`FetchProvider`, `FetchRunProgress`, `FetchRunRecord`, `FetchServiceConfig`, `FetchServiceState`, `POLL_INTERVAL_MS`, `GRAPH_REFRESH_INTERVAL_MS`, `runTimestampValue`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Loader2, PlayCircle, Plus, X } from 'lucide-react';`；`import { Switch } from '../Switch';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/PersonalContext/ServicesPanel.tsx#L1-L735)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/PersonalContext/SettingsPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c42acd7cd31d8b329636332ccfac56bf1e5cba26060aa7a77627ab6b9ff68664 -->
**`jiuwenswarm/channels/web/frontend/src/components/PersonalContext/SettingsPanel.tsx`**

- 源码声明的类型、组件或调用边界：`PersonalContextSettingsPanelProps`, `isRequestTimeoutError`, `isRepositoryCredentialError`, `PersonalContextSettingsPanel`, `availableModels`, `visibleModels`, `currentModelName`, `masterEnabled`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Loader2, X } from 'lucide-react';`；`import { Switch } from '../Switch';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/PersonalContext/SettingsPanel.tsx#L1-L686)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/PersonalContext/edgeBookmarkFolders.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e107b6982d9c0d4bb7aa8dd9f9821d2fe228cc30cc210711bd3d6ac1f7fdf76b -->
**`jiuwenswarm/channels/web/frontend/src/components/PersonalContext/edgeBookmarkFolders.ts`**

- 源码声明的类型、组件或调用边界：`parseEdgeBookmarkFolderPaths`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/PersonalContext/edgeBookmarkFolders.ts#L1-L3)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/PersonalContext/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0b8be5dd103879102ddb7e01e608182e6b01ca2cb61790868e39f48157cb8957 -->
**`jiuwenswarm/channels/web/frontend/src/components/PersonalContext/index.tsx`**

- 源码声明的类型、组件或调用边界：`PersonalContextPanelProps`, `PersonalContextPanel`, `hasFetchServices`, `hasGraphNodes`, `hasContent`, `showIntro`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect } from 'react';`；`import { usePersonalContextStore } from '../../stores';`；`import { PersonalContextGraphPanel } from './GraphPanel';`；`import { PersonalContextServicesPanel } from './ServicesPanel';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/PersonalContext/index.tsx#L1-L70)。
<!-- /kb:file -->
