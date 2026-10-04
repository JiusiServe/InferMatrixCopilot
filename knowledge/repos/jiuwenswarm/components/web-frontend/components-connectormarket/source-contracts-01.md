---
title: "components-connectormarket 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-connectormarket 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/Buttons.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=68f0f47e47cab0c17f65678feec6f0ef92abeb4276b9da1139d15201e4942650 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/Buttons.tsx`**

- 源码声明的类型、组件或调用边界：`PillButton`, `DetailLinkButton`, `IconAvatar`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/Buttons.tsx#L1-L68)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/CliAuthModal.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=98701eb81a784f4dae3a75cf1e2c5a9fa3c0f0061386d188f22471bcac3b9f3e -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/CliAuthModal.tsx`**

- 源码声明的类型、组件或调用边界：`CliAuthModalProps`, `CliAuthModal`, `waitAuth`, `requestSeqRef`, `seq`, `handleManualOpen`, `handleRetry`, `handleCancel`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useRef, useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`；`import { X, ExternalLink, Loader2, CheckCircle2, RotateCw } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/CliAuthModal.tsx#L1-L176)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/ConfirmDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ecf1377d28acf865aea61c1c1cc6812f73734fcedd620527759272ec561f416c -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/ConfirmDialog.tsx`**

- 源码声明的类型、组件或调用边界：`ConfirmDialogProps`, `ConfirmDialog`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/ConfirmDialog.tsx#L1-L51)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/ConnectTokenModal.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=28eeb1db1604e60827282ab7fe664f18c72d3257ba2344c9e1554fdf5fb085df -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/ConnectTokenModal.tsx`**

- 源码声明的类型、组件或调用边界：`ConnectTokenModalProps`, `ConnectTokenModal`, `saveCredentialsAndConnect`, `requiredTokens`, `fields`, `allFilled`, `avatar`, `handleSubmit`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`；`import { X, Loader2, ExternalLink } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/ConnectTokenModal.tsx#L1-L155)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/CreatePluginPage.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e4849a3800b8bb9bc41d00d1fbb81728043a0bc549e966d6fab93867ca520741 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/CreatePluginPage.tsx`**

- 源码声明的类型、组件或调用边界：`PickerItem`, `DESCRIPTION_MAX`, `AVATAR_UPLOAD_ENABLED`, `RequiredFieldKey`, `SkillItem`, `InstalledPluginItem`, `CreatePluginPageProps`, `toSkillPickerItems`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useMemo, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { ImagePlus, Trash2, Plus } from 'lucide-react';`；`import { webRequest } from '../../services/webClient';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/CreatePluginPage.tsx#L1-L450)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/EntityAvatar.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ee5aa60fb69532b7b813d63c62c2f3efae88c96cd0196feb359c6d7f40b70d8f -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/EntityAvatar.tsx`**

- 源码声明的类型、组件或调用边界：`EntityAvatarProps`, `EntityAvatar`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import type { AvatarStyle } from '../../utils/skillAvatar';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/EntityAvatar.tsx#L1-L28)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/FormPageLayout.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8d3d634c5b8c618b0e832a62f50eb344796364a3b292b8241d357b2d28a58754 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/FormPageLayout.tsx`**

- 源码声明的类型、组件或调用边界：`FormPageLayoutProps`, `FormPageLayout`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { ChevronLeft, Loader2 } from 'lucide-react';`；`import './FormPageLayout.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/FormPageLayout.tsx#L1-L91)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/MarketCard.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6aa26e1f639572f12ea3a27bbf9c9df9702feeb4ba70f2f4816242e5b10b63a3 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/MarketCard.tsx`**

- 源码声明的类型、组件或调用边界：`MarketCardProps`, `MarketCard`, `avatarProp`, `titleEndNode`, `actionSlot`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import './ConnectorMarket.css';`；`import { Loader2, AlertCircle } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import { PageCard } from '../ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/MarketCard.tsx#L1-L99)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/MarketplacePage.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=68ce64a533b5bd81e986ea7a1e852382b90dc00a3bca2e217137b19e8cc6ba99 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/MarketplacePage.tsx`**

- 源码声明的类型、组件或调用边界：`InstallationFilter`, `PluginPackageSummary`, `MarketKind`, `TopTab`, `MarketplacePageProps`, `CATEGORY_TOP_N`, `PAGE_SIZE_ALL`, `PAGE_SIZE_OPTIONS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import SimpleSelect from '../CronPanel/SimpleSelect';`；`import { InstallationFilterSelect, matchesInstallation, type InstallationFilter } from '../marketpla`；`import { catalogCacheOf } from '../../features/catalogCache';`；`import { CatalogCacheNotice } from '../marketplace/CatalogCacheNotice';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/MarketplacePage.tsx#L1-L845)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/McpDetailPage.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ddc4a1a0e5cd3ae560ba739fa4654a8c401486e268d27255212be18b4821e825 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/McpDetailPage.tsx`**

- 源码声明的类型、组件或调用边界：`integrationTypeLabelKey`, `McpDetailPageProps`, `McpDetailPage`, `connector`, `runtimeName`, `detail`, `tools`, `skills`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { PublicationDetailStatus } from '../marketplace/PublicationDetailStatus';`；`import { openAssetPublish } from '../../features/assetPublishEvents';`；`import { canShowAssetPublish } from '../../features/assetPublishState';`；`import { useEffect, useState } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/McpDetailPage.tsx#L1-L548)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/MyMarketCard.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=05ce8ac30bc63b58d8a306008cbefe6bab3c1ea8475e374943c4dd1f9e6a5aa2 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/MyMarketCard.tsx`**

- 源码声明的类型、组件或调用边界：`MyMarketCardProps`, `MyMarketCard`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { MarketCard } from './MarketCard';`；`import type { McpCardState } from './mcpState';`；`import type { McpBusyKind } from '../../types/connector';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/MyMarketCard.tsx#L1-L35)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/PickerModal.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b58b128cc99e952e5f32192efe7ed37634c25dd953fbd942f626594a9c273497 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/PickerModal.tsx`**

- 源码声明的类型、组件或调用边界：`PickerItem`, `PickerModalProps`, `PickerModal`, `visible`, `q`, `toggle`, `checked`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Search, Plus, Check } from 'lucide-react';`；`import { FormDrawer, PageCard } from '../ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/PickerModal.tsx#L1-L99)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/PluginDetailPage.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f723687e47df444e6dc029cf7f04dde047be515984cf29297a022e2d477a53e9 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/PluginDetailPage.tsx`**

- 源码声明的类型、组件或调用边界：`PluginDetailPageProps`, `PluginDetailPage`, `detail`, `loadDetail`, `storeBusy`, `installed`, `connectionState`, `installPending`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { PublicationDetailStatus } from '../marketplace/PublicationDetailStatus';`；`import { openAssetPublish } from '../../features/assetPublishEvents';`；`import { canShowAssetPublish } from '../../features/assetPublishState';`；`import { useEffect, useState } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/PluginDetailPage.tsx#L1-L422)。
<!-- /kb:file -->
