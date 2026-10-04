---
title: "components-marketplace 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-marketplace 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/marketplace/CatalogCacheNotice.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3944913fb4ceb635c9c1468de43cf1ea1c590a9427e69b06d374b3ba3d4f078e -->
**`jiuwenswarm/channels/web/frontend/src/components/marketplace/CatalogCacheNotice.tsx`**

- 源码声明的类型、组件或调用边界：`CatalogCacheMetadata`, `CatalogCacheNotice`, `notice`, `zh`, `text`, `updatedText`, `updatedTimestamp`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/marketplace/CatalogCacheNotice.tsx#L1-L37)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/marketplace/InstallationFilterSelect.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=40dbf922c186e5c136640f28b5c8059c1db6e30863ded3f9d27fb75c106f9026 -->
**`jiuwenswarm/channels/web/frontend/src/components/marketplace/InstallationFilterSelect.tsx`**

- 源码声明的类型、组件或调用边界：`InstallationFilter`, `matchesInstallation`, `InstallationFilterSelect`, `zh`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { FilterDropdown } from '../SkillPanel/SkillPanelWidgets';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/marketplace/InstallationFilterSelect.tsx#L1-L39)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/marketplace/MarketplaceSurface.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ca730b8e48ca78078f4da84c4cd433d5cda6a214ed211101b68697fc381775e0 -->
**`jiuwenswarm/channels/web/frontend/src/components/marketplace/MarketplaceSurface.tsx`**

- 源码声明的类型、组件或调用边界：`MarketplaceSurfaceProps`, `MarketplaceSurface`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode, Ref } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/marketplace/MarketplaceSurface.tsx#L1-L23)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/marketplace/PublicationDetailStatus.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5171337bdc7311f4b1e3f93b27eeda2a1c2f7dd1e1172a935f680663de06b062 -->
**`jiuwenswarm/channels/web/frontend/src/components/marketplace/PublicationDetailStatus.tsx`**

- 源码声明的类型、组件或调用边界：`PublicationDetailStatus`, `lookup`, `label`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import { useAssetPublication } from '../../hooks/useAssetPublication';`；`import { publicationDetailLabel } from '../../features/assetPublication';`；`import type { PublishAssetKind } from '../../types/assetPublish';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/marketplace/PublicationDetailStatus.tsx#L1-L10)。
<!-- /kb:file -->
