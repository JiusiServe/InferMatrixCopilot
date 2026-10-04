---
title: "features-settings 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-settings 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/archivedTasks/ArchivedTasksSettings.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2f6f872b320f027a2ba6d9c1e59f999a2f681657fc7bea2cec6786ede67615a8 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/archivedTasks/ArchivedTasksSettings.tsx`**

- 源码声明的类型、组件或调用边界：`ArchivedSession`, `SEARCH_DEBOUNCE_MS`, `DeleteTarget`, `actionErrorKey`, `code`, `ArchivedTasksSettingsModule`, `ArchivedTasksSettingsPanel`, `workMode`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Archive, CircleAlert, Folder, Loader2, RotateCcw, Search, Trash2 } from 'lucide-react';`；`import { Button, Input, toast } from '../../../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/archivedTasks/ArchivedTasksSettings.tsx#L1-L431)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/archivedTasks/definition.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9e12e4183696e60628a24bcff3232bd19423365cf0e823dafd3e8c3004f437a9 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/archivedTasks/definition.ts`**

- 源码声明的类型、组件或调用边界：`archivedTasksModule`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Archive } from 'lucide-react';`；`import type { SettingsModuleDefinition } from '../../registry/types';`；`import { ArchivedTasksSettingsModule } from './ArchivedTasksSettings';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/archivedTasks/definition.ts#L1-L17)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/archivedTasks/useArchivedTaskLists.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9da0a968398807b3818353d59c6f4b79bd1b28443790bcd7d43afbb12794a56f -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/archivedTasks/useArchivedTaskLists.ts`**

- 源码声明的类型、组件或调用边界：`ArchivedListParams`, `ArchivedListResponse`, `ArchivedSession`, `PAGE_SIZE`, `EVENT_REFRESH_DEBOUNCE_MS`, `ARCHIVE_EVENT_NAMES`, `ResourceListState`, `createInitialListState`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useRef, useState } from 'react';`；`import { webClient } from '../../../../services/webClient';`；`import {`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/archivedTasks/useArchivedTaskLists.ts#L1-L177)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/browser/definition.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=577eec62225a2dbbd2a5e40014c3c556e31ac8a53fe51c26661347e53be033c3 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/browser/definition.ts`**

- 源码声明的类型、组件或调用边界：`browserModule`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { settingsNavigationIcons } from '../../../../assets/settings';`；`import type { SettingsModuleDefinition } from '../../registry/types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/browser/definition.ts#L1-L26)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/ChannelsModule.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4176b3d4e8279575848da2dfb00a606adde41ea0349b29730a4d5965c976e2ab -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/ChannelsModule.tsx`**

- 源码声明的类型、组件或调用边界：`ChannelsModule`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { SettingsChannelsPanel } from './SettingsChannelsPanel';`；`import { useSettingsServices } from '../../services/SettingsServicesProvider';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/ChannelsModule.tsx#L1-L19)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/SettingsChannelsPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d581c611b133b9ec5faae260c4649845118d209d63c1629aee25e5810a4824f5 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/SettingsChannelsPanel.tsx`**

- 源码声明的类型、组件或调用边界：`SettingsChannelsPanelProps`, `SettingsChannelsPanel`, `controller`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import { Button } from '../../../../components/ui';`；`import { SettingsConfirmDialog } from '../../components';`；`import { ChannelConfigDialog } from './components/ChannelConfigDialog';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/SettingsChannelsPanel.tsx#L1-L97)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelAdapters.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=accd3d2c1d180780f05eaafebe841611c2b87875939d46ccb82ebe7e3498c980 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelAdapters.ts`**

- 源码声明的类型、组件或调用边界：`DEFAULT_FEISHU_CONFIG`, `DEFAULT_XIAOYI_CONFIG`, `normalizeStringList`, `normalizeTextList`, `normalizeFeishuConfig`, `data`, `normalizeFeishuApp`, `config`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import i18n from '../../../../i18n';`；`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelAdapters.ts#L1-L378)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelCatalog.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6d29f4897353b859fdeea225dd944f6c71ccf35c0cb86f59e31c71794e441e90 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelCatalog.ts`**

- 源码声明的类型、组件或调用边界：`SETTINGS_CHANNEL_IDS`, `CHANNEL_LOGOS`, `normalizeEnabledChannels`, `channelId`, `buildSettingsChannels`, `enabledChannels`, `getSettingsChannelLogo`, `getSettingsChannelLabel`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TFunction } from 'i18next';`；`import { settingsChannelLogos } from '../../../../assets/settings';`；`import type { ChannelItem, SettingsChannelId } from './channelTypes';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelCatalog.ts#L1-L51)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelFormItems.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e6b5f1c98bc8259e4da1a80103f2b3943d719df5e1409ca1e43b9d225ced7798 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelFormItems.ts`**

- 源码声明的类型、组件或调用边界：`passwordLabels`, `switchLabel`, `withFieldRequirements`, `createXiaoyiFormItems`, `createFeishuAppFormItems`, `createDingtalkFormItems`, `createTelegramFormItems`, `createDiscordFormItems`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { TFunction } from 'i18next';`；`import type { FormItem, FormValues } from '../../../../components/form';`；`import { isChannelFormFieldOptional } from './channelRequirements';`；`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelFormItems.ts#L1-L324)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelGuideUrls.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d746d88f1bd6167bbe07578c396d4e42ecf409c96bc5100af8b139db407d4ffe -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelGuideUrls.ts`**

- 源码声明的类型、组件或调用边界：`ChannelGuideLanguage`, `CHANNEL_GUIDE_DOCS_VERSION`, `CHANNEL_GUIDE_BASE_URL`, `CHANNEL_GUIDE_PATHS`, `getSettingsChannelGuideUrl`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { SettingsChannelId } from './channelTypes';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelGuideUrls.ts#L1-L31)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelRequirements.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d0c360ba54ffa429f9390cedccc6b6b583b0ea9602fc0d215097645feef8a591 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelRequirements.ts`**

- 源码声明的类型、组件或调用边界：`FieldRequirement`, `ChannelFormValuesById`, `ChannelFieldRequirements`, `CHANNEL_FIELD_REQUIREMENTS`, `satisfies`, `shouldConfirmXiaoyiEnable`, `getFieldRequirement`, `requirement`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { FormRule, FormRules, FormValues } from '../../../../components/form';`；`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelRequirements.ts#L1-L167)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelTypes.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=48e9ebf0ffd40a4e0497752cff3f0c135af07c6eac5758573edaac759b136dd6 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelTypes.ts`**

- 源码声明的类型、组件或调用边界：`SettingsChannelId`, `SingleSettingsChannelId`, `ChannelItem`, `FeishuConfig`, `FeishuAppConfig`, `FeishuAppDraft`, `FeishuFormValues`, `XiaoyiConfig`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/channelTypes.ts#L1-L113)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/components/ChannelConfigDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ba95654d842c6bfb415b597bca18a6367cc0e775bb72adbd720484a25c29832c -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/components/ChannelConfigDialog.tsx`**

- 源码声明的类型、组件或调用边界：`RefObject`, `FeishuChannelFormHandle`, `SettingsChannelControllers`, `ChannelFormContent`, `ChannelConfigDialog`, `feishuFormRef`, `controller`, `label`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useRef, type RefObject } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { FormDialog } from '../../../../../components/form';`；`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/components/ChannelConfigDialog.tsx#L1-L119)。
<!-- /kb:file -->
