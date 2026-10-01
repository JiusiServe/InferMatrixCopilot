---
title: "components-skillpanel 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-skillpanel 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/DocToSkillModal.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a0e77ca83f4aa90399df35dd85880058ef91e2a12de1b786407324289a1335ec -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/DocToSkillModal.tsx`**

- 源码声明的类型、组件或调用边界：`DocToSkillModalProps`, `DocToSkillModal`, `isDocConfirmDisabled`, `file`, `file`, `rect`, `file`, `link`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { HelpCircle, Upload } from 'lucide-react';`；`import { TopAnchorTooltip } from './SkillPanelWidgets';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/DocToSkillModal.tsx#L1-L190)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/MarketplaceView.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9b8cda835c0b884b0e71c003f9281aae0a68eeb8a48b413278c92c6bdcf45120 -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/MarketplaceView.tsx`**

- 源码声明的类型、组件或调用边界：`CatalogCacheMetadata`, `PageCardActionProps`, `MarketplaceViewProps`, `MarketplaceView`, `moreItems`, `SkillPacksView`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { catalogAwaitingItems, type CatalogCacheMetadata } from '../../features/catalogCache';`；`import { useTranslation } from 'react-i18next';`；`import { ChevronRight, Loader2 } from 'lucide-react';`；`import BackIcon from '../../assets/work-mode/arrow-left.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/MarketplaceView.tsx#L1-L315)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/SkillDetailView.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=53f4e61d40b2e4ba8fc772bc8d032a29fcab521aebec0d87fb5b777caa468b95 -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/SkillDetailView.tsx`**

- 源码声明的类型、组件或调用边界：`EntityHeaderAvatar`, `FilePreviewContentFile`, `FilePreviewTreeNode`, `buildSkillPreviewFile`, `matched`, `skillDir`, `downloadUrl`, `MEMBER_BLOCKING_REASON_KEYS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { openAssetPublish } from '../../features/assetPublishEvents';`；`import { useTranslation } from 'react-i18next';`；`import type { ReactNode } from 'react';`；`import BackIcon from '../../assets/work-mode/arrow-left.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/SkillDetailView.tsx#L1-L806)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/SkillGraphTab.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4de89f6fad8a549ab793f98ea4d4b8da42454e1d6c1e1a3839033b77f33fd455 -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/SkillGraphTab.tsx`**

- 源码声明的类型、组件或调用边界：`SkillGraphPanelHandle`, `SkillGraphTabProps`, `SkillGraphTab`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { MutableRefObject } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Loader2, Music2 } from 'lucide-react';`；`import { SkillGraphPanel, type SkillGraphPanelHandle } from '../SkillGraphPanel';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/SkillGraphTab.tsx#L1-L93)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/SkillPanelWidgets.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7699d67c37763446fcd6287cfeb0438fe04a87db413263737dddea632ebe76ec -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/SkillPanelWidgets.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `PageCardActionProps`, `FormFieldTooltip`, `ref`, `handleEnter`, `rect`, `handleLeave`, `TopAnchorTooltip`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useRef, useState, type ReactNode } from 'react';`；`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`；`import { ChevronRight } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/SkillPanelWidgets.tsx#L1-L273)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/SkillToasts.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7316e32dacdf2049a8d50c195370f668997d0bb99156084b8009fc7873e2b392 -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/SkillToasts.tsx`**

- 源码声明的类型、组件或调用边界：`SkillToastsProps`, `SkillToasts`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import type { SkillToastType } from './useSkillToasts';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/SkillToasts.tsx#L1-L112)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/UploadSkillModal.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=db249d04d6700669ffad92d73b37325dcae84d7606f7bb5f1e34e22c3c633d4b -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/UploadSkillModal.tsx`**

- 源码声明的类型、组件或调用边界：`UploadSkillModalProps`, `UploadSkillModal`, `file`, `file`, `file`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import TipIcon from '../../assets/tip.svg?react';`；`import UpFileIcon from '../../assets/upFile.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/UploadSkillModal.tsx#L1-L118)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1818c62ad07c1d01dda09753667a4be56552c27cbf085e285fadd28d56b07381 -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/index.tsx`**

- 源码声明的类型、组件或调用边界：`MarketplaceSubView`, `errorToMessage`, `MY_SKILLS_EMPTY_KEY`, `MySkillsGroupHeader`, `CreateSkillMenu`, `SkillPanel`, `prevIsActiveRef`, `mountedRef`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { publicationLabel, matchesPublicationFilter } from '../../features/assetPublication';`；`import { CatalogCacheNotice } from '../marketplace/CatalogCacheNotice';`；`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/index.tsx#L1-L1607)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/skillPanelUtils.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7ab6ad1945144a02bcf3bd201d9496c1930799d54282cad2d849e7abebe6025a -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/skillPanelUtils.ts`**

- 源码声明的类型、组件或调用边界：`SKILLS_FETCH_TIMEOUT_REFRESH_MS`, `SKILLS_FETCH_TIMEOUT_NORMAL_MS`, `GRAPH_READING_MIN_VISIBLE_MS`, `SKILL_NAME_PATTERN`, `SKILL_NAME_MAX_LEN`, `VERSION_PATTERN`, `DISPLAY_NAME_MAX_LEN`, `PREVIEWABLE_MIME_TYPES`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { MarketplacePluginItem, SkillItem } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/skillPanelUtils.ts#L1-L125)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/skillRetrievalStatus.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=db1aa4ed88207ca3ccdb162c3f00914d6180e3dcca6f0011ecde8ad47a77c751 -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/skillRetrievalStatus.ts`**

- 源码声明的类型、组件或调用边界：`SkillRetrievalBuildStatus`, `SkillRetrievalCandidateScale`, `SkillRetrievalStrategy`, `SkillRetrievalStatus`, `SkillRetrievalStatusContractError`, `isRecord`, `requireNonNegativeInteger`, `requireString`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/skillRetrievalStatus.ts#L1-L161)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/skillVersionOptions.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e6d388ce5231794589d5f8015840ff0bcbddb6ddb2a4d95de6aa71d79fbecd88 -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/skillVersionOptions.ts`**

- 源码声明的类型、组件或调用边界：`SkillVersionOptionSource`, `SkillVersionOption`, `buildSkillVersionOptions`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/skillVersionOptions.ts#L1-L23)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/symphonyGraphAction.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5441d414abe1ae1b896719a40677754a5c7a24971592672e6a0241586f32b04c -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/symphonyGraphAction.ts`**

- 源码声明的类型、组件或调用边界：`GraphActionResponse`, `SymphonyGraphPanelHandle`, `GraphActionRequest`, `SymphonyEnabledChangeResult`, `CoordinateSymphonyEnabledChangeInput`, `errorMessage`, `coordinateSymphonyEnabledChange`, `appliedWithoutRestart`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/symphonyGraphAction.ts#L1-L90)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6d1e430b5a0b14c8d28a2383912d2892517b3b7a76ac944b8684e0047ced255e -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/types.ts`**

- 源码声明的类型、组件或调用边界：`FileTreeNode`, `SkillItem`, `SkillPackBlockedMember`, `SkillPackMember`, `SkillPackProjection`, `InstalledPluginItem`, `SkillDetail`, `HubSkillDetailData`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/types.ts#L1-L238)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useSkillToasts.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=26babe38269139e85eb610d702ac26f4b0d78285c2c60fd26f9c7d84fa71c5ce -->
**`jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useSkillToasts.ts`**

- 源码声明的类型、组件或调用边界：`SkillToastType`, `SkillToastShower`, `useSkillToasts`, `messageTimerRef`, `showMessage`, `displayText`, `duration`, `cleanMessage`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useRef, useState } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/SkillPanel/useSkillToasts.ts#L1-L48)。
<!-- /kb:file -->
