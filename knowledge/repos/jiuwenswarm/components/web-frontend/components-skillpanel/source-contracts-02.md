---
title: "components-skillpanel 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-skillpanel 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useEvolution.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7ad15cf31ae2887f979c833789de6be8883a508f0fa13598dbd30c83bda8b353 -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useEvolution.ts`**

- 源码声明的类型、组件或调用边界：`UseEvolutionParams`, `useEvolution`, `evolutionSaveTimerRef`, `sortedEvolutionEntries`, `ta`, `tb`, `fetchEvolutionEntries`, `data`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { webRequest } from '../../services/webClient';`；`import type { EvolutionEntry, EvolutionGetResponse, LoadState, SkillDetail } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useEvolution.ts#L1-L144)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useHubMarketplace.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dda116d83d511c1ab820960eeaa2fe685d7d19ad17b4db905aab231c29bc3397 -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useHubMarketplace.ts`**

- 源码声明的类型、组件或调用边界：`CatalogCacheMetadata`, `CatalogItems`, `HUB_HOME_TOP_K`, `HUB_MORE_TOP_K`, `HubRecommendSkill`, `mapRecommendSkill`, `WithSessionFn`, `SkillPanelTab`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { webRequest } from '../../services/webClient';`；`import type { HubSkillDetail, LoadState, MarketplacePluginItem } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useHubMarketplace.ts#L1-L604)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useRetrievalIndexBuild.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c49d98e43bced4e46c9dec22639117004de826c4564579c85084991639dba452 -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useRetrievalIndexBuild.ts`**

- 源码声明的类型、组件或调用边界：`UseRetrievalIndexBuildParams`, `useRetrievalIndexBuild`, `startRetrievalIndexBuild`, `statusPayload`, `status`, `payload`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { webRequest } from '../../services/webClient';`；`import { canBuildSkillRetrievalIndex, parseSkillRetrievalStatus } from './skillRetrievalStatus';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useRetrievalIndexBuild.ts#L1-L47)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useSkillFilesTab.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f2f743a1e2f0a9b66c0832dd514f6539e3d9dd67a310f22b1db963f4c8e95aff -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useSkillFilesTab.tsx`**

- 源码声明的类型、组件或调用边界：`FilePreviewTreeNode`, `WithSessionFn`, `UseSkillFilesTabParams`, `MutablePreviewNode`, `toPreviewTreeNodes`, `root`, `dirMap`, `entry`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useMemo, useRef, useState } from 'react';`；`import { webRequest } from '../../services/webClient';`；`import { isFilePreviewable } from './skillPanelUtils';`；`import { findDefaultPreviewFile, type FilePreviewTreeNode } from '../ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useSkillFilesTab.tsx#L1-L146)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useSymphonyGraph.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b02f923ed8fecf1b24e98123fc66d3c08d5ec41e42da577c23ff6862239b514d -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useSymphonyGraph.ts`**

- 源码声明的类型、组件或调用边界：`UseSymphonyGraphParams`, `useSymphonyGraph`, `skillGraphPanelRef`, `graphReadingStartedAtRef`, `graphReadingTimerRef`, `clearGraphActionError`, `updateSymphonyEnabled`, `result`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { webRequest } from '../../services/webClient';`；`import type { SkillGraphPanelHandle } from '../SkillGraphPanel';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useSymphonyGraph.ts#L1-L124)。
<!-- /kb:file -->
