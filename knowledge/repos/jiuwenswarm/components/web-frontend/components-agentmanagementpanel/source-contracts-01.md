---
title: "components-agentmanagementpanel 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-agentmanagementpanel 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentEditor.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e3f328b61587bb930db02058aa7d536606dacfdfe6bc01ba5a6a3797d95872b2 -->
**`jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentEditor.tsx`**

- 源码声明的类型、组件或调用边界：`FormEvent`, `AgentDraft`, `McpOption`, `RequestStatus`, `SkillOption`, `AgentEditorProps`, `AgentEditor`, `personaSurfaceRef`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Check, ChevronDown, ChevronUp, Minus, Plus, Trash2 } from 'lucide-react';`；`import { useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import SearchIcon from '../../assets/agent-management/agent-search.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentEditor.tsx#L1-L795)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentGroupDetailPage.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a49d8ab7bdf2f9cdbcc25ec6b43c846cf1dc97004054e0bb2e61f76f67fa999f -->
**`jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentGroupDetailPage.tsx`**

- 源码声明的类型、组件或调用边界：`AgentGroupDetailPageProps`, `AgentGroupDetailPage`, `canUse`, `canDelete`, `canPreviewFiles`, `category`, `categoryLabel`, `detailTags`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import { openAssetPublish } from '../../features/assetPublishEvents';`；`import { canShowAssetPublish } from '../../features/assetPublishState';`；`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentGroupDetailPage.tsx#L1-L385)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentGroupEditor.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6ac049c7e3a219125f5fe54addac4e49ac3fe325ebc4c9e40663e369d836aa02 -->
**`jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentGroupEditor.tsx`**

- 源码声明的类型、组件或调用边界：`FormEvent`, `AgentCatalogItem`, `AgentGroupDraft`, `RequestStatus`, `SkillOption`, `AgentGroupEditorProps`, `AgentGroupEditor`, `leaderPickerTriggerRef`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo, useRef, useState, type FormEvent, type ReactNode } from 'react';`；`import { ArrowLeftRight, Check, ChevronDown, ChevronUp, Minus, Plus, Trash2 } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentGroupEditor.tsx#L1-L634)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentGroupMemberPicker.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0af203155a5f0eeb2843157b485bad16f8e818cd4b577e437cac6f71a57e21a3 -->
**`jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentGroupMemberPicker.tsx`**

- 源码声明的类型、组件或调用边界：`AgentCatalogItem`, `RequestStatus`, `AgentGroupMemberPickerProps`, `AgentOptionAvatar`, `avatarUrl`, `AgentGroupMemberPicker`, `filteredAgents`, `normalized`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo, useState } from 'react';`；`import { Check, LoaderCircle, Plus } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentGroupMemberPicker.tsx#L1-L250)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentGroupUploadDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4b1dab42d71d9f2f9020764eabfaeb6184846abdfe543e88848b8866b3be7d6c -->
**`jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentGroupUploadDialog.tsx`**

- 源码声明的类型、组件或调用边界：`LocalFilePick`, `AgentGroupUploadDialogProps`, `DROP_ACCEPT_WINDOW_MS`, `formatFileSize`, `units`, `index`, `size`, `pickFromDroppedFile`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createPortal } from 'react-dom';`；`import { useCallback, useEffect, useRef, useState } from 'react';`；`import { FileArchive, Info, Loader2, X } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentGroupUploadDialog.tsx#L1-L336)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentTagPicker.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cff3eccbd2e170cf5a8a8d930d1177258ab93f1423b032fb7ab083d898876b96 -->
**`jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentTagPicker.tsx`**

- 源码声明的类型、组件或调用边界：`AgentTagPickerProps`, `AgentTagPicker`, `pickerRef`, `valuesRef`, `valueSignature`, `updateScrollState`, `values`, `values`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';`；`import { Check, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import { AGENT_TAG_OPTIONS } from '../../features/agentManagement/tagOptions';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentTagPicker.tsx#L1-L222)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentUploadDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dd33074663b5bbf4e7464c3f74d48d668f9d3303f25b36b19c37bf1898d1c7b3 -->
**`jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentUploadDialog.tsx`**

- 源码声明的类型、组件或调用边界：`LocalFilePick`, `AgentUploadDialogProps`, `DROP_ACCEPT_WINDOW_MS`, `formatFileSize`, `units`, `unitIndex`, `size`, `pickFromDroppedFile`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createPortal } from 'react-dom';`；`import { useCallback, useEffect, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { FileArchive, Info, Loader2, X } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/AgentUploadDialog.tsx#L1-L294)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/CatalogPage.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0b1192853e394abb82bb6d185cb73d3eab06f0cea7c8aa5a765f076afdf98115 -->
**`jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/CatalogPage.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `AgentCatalogItem`, `AGENT_PAGE_SIZE`, `CATEGORIES`, `CatalogPageProps`, `CatalogPage`, `isMine`, `totalPages`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { type ReactNode } from 'react';`；`import { ChevronLeft, ChevronRight, LoaderCircle } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import { type AgentCatalogItem, type RequestStatus } from '../../features/agentManagement';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/CatalogPage.tsx#L1-L254)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/DefinitionCard.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=90d488f5f1d6c7b3a55bda2b9de4b47964bbb2abdf83d3fd52c4b27cadc8d22e -->
**`jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/DefinitionCard.tsx`**

- 源码声明的类型、组件或调用边界：`AgentCatalogItem`, `DefinitionCardProps`, `getAvatarLetter`, `TagSummaryProps`, `TagSummary`, `metaRef`, `measureRef`, `tagList`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useLayoutEffect, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Ellipsis } from 'lucide-react';`；`import { getAgentAvatarUrl, type AgentCatalogItem } from '../../features/agentManagement';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/DefinitionCard.tsx#L1-L256)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/DefinitionDetailPage.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9c85da202c6c8b9c0fbece8dfe8b551c1b8e5767c255b5b2ae2887408775d2fe -->
**`jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/DefinitionDetailPage.tsx`**

- 源码声明的类型、组件或调用边界：`AgentFileContent`, `AgentDetail`, `DefinitionFileEntry`, `RequestStatus`, `DefinitionDetailPageProps`, `DefinitionDetailPage`, `loading`, `avatarUrl`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { PublicationDetailStatus } from '../marketplace/PublicationDetailStatus';`；`import { openAssetPublish } from '../../features/assetPublishEvents';`；`import { canShowAssetPublish } from '../../features/assetPublishState';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/DefinitionDetailPage.tsx#L1-L363)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/DefinitionFilePreview.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f2dd922c00935f6d2201b2e10dd50fb98140b3aa9065e76dc76ce7730faf445f -->
**`jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/DefinitionFilePreview.tsx`**

- 源码声明的类型、组件或调用边界：`FilePreviewContentFile`, `FilePreviewTreeNode`, `DefinitionFilePreviewProps`, `toPreviewTreeNodes`, `findDefaultDefinitionFile`, `DefinitionFilePreview`, `nodes`, `selectedIsPreviewable`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import type { AgentFileContent, DefinitionFileEntry, RequestStatus } from '../../features/agentManag`；`import { isPreviewableFile } from '../../features/agentManagement';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/AgentManagementPanel/DefinitionFilePreview.tsx#L1-L116)。
<!-- /kb:file -->
