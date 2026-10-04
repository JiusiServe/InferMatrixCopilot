---
title: "features-settings 源码接口与集成边界 04"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-settings 源码接口与集成边界 04

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/experimental/definition.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4133f84ef9546f7652e1c8c94eb93505cbe09da1294933cf4c81232c1e28939c -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/experimental/definition.ts`**

- 源码声明的类型、组件或调用边界：`experimentalModule`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { settingsNavigationIcons } from '../../../../assets/settings';`；`import type { SettingsModuleDefinition } from '../../registry/types';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/experimental/definition.ts#L1-L71)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/experimental/externalCliInstallState.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b5e0ccf02363254d979d6966fcbe5ea510fb31b49c564edc88f33cf32043ec27 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/experimental/externalCliInstallState.ts`**

- 源码声明的类型、组件或调用边界：`ExternalCliPendingChoices`, `ExternalCliInstallStatuses`, `ExternalCliPendingChoiceStorage`, `EXTERNAL_CLI_PENDING_CHOICES_STORAGE_KEY`, `EXTERNAL_CLI_AGENT_KINDS`, `browserSessionStorage`, `normalizePendingChoice`, `candidate`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ExternalCliAgentKind, ExternalCliPendingChoice } from '../../../../components/External`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/experimental/externalCliInstallState.ts#L1-L99)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/general/GeneralSettings.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=00bf7e917a3751731d0f68737a441e9cf657c24741aa09bfe12779c077807de8 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/general/GeneralSettings.tsx`**

- 源码声明的类型、组件或调用边界：`TagVariant`, `ConnectionStatusSetting`, `connectionKey`, `connectionVariant`, `CloseAction`, `isCloseAction`, `closeActionApi`, `api`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Select, Tag, type TagVariant } from '../../../../components/ui';`；`import { SettingRow } from '../../components';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/general/GeneralSettings.tsx#L1-L108)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/general/definition.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ae9c51c9a881fc47cade52fdaefab1a9e2d9cd60e552cca1eb85ddecb80258ed -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/general/definition.ts`**

- 源码声明的类型、组件或调用边界：`generalModule`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { settingsNavigationIcons } from '../../../../assets/settings';`；`import type { SettingsModuleDefinition } from '../../registry/types';`；`import { ConnectionStatusSetting } from './GeneralSettings';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/general/definition.ts#L1-L27)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ContextWindowField.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=22f2523db0e2b5cc1fd80e3898c61feabbb892355a25dd0533eafb6ed12e4ef6 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ContextWindowField.tsx`**

- 源码声明的类型、组件或调用边界：`ContextWindowFieldProps`, `ContextWindowField`, `currentValue`, `currentTokens`, `selected`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Button, Input } from '../../../../components/ui';`；`import { CONTEXT_WINDOW_PRESETS, parseContextWindowTokens } from './contextWindow';`；`import './ContextWindowField.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ContextWindowField.tsx#L1-L67)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/FreeModelSettingsDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cb15d826724fa2de8972a0cbddc0b9646ae49179a24ed6ea966994fba3b0558a -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/FreeModelSettingsDialog.tsx`**

- 源码声明的类型、组件或调用边界：`FreeModelSettingsDialog`, `titleId`, `setAvailableModels`, `valueOf`, `hasInvalid`, `save`, `changes`, `model`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useId, useMemo, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { X } from 'lucide-react';`；`import { Button, Dialog } from '../../../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/FreeModelSettingsDialog.tsx#L1-L148)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/FreeModelsSettings.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fecba7c9b49e7124062aa425895de44fa4d8e6b5b1232a760ae625d06587f25d -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/FreeModelsSettings.tsx`**

- 源码声明的类型、组件或调用边界：`QuotaView`, `PointsHeadline`, `status`, `value`, `unit`, `PointsHint`, `reset`, `hasUsage`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useMemo, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { ChevronRight, LogIn } from 'lucide-react';`；`import { Tag } from '../../../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/FreeModelsSettings.tsx#L1-L279)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ModelDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bec03cbc846b4262f6be90db653415c6c31b38ccc275e836f79a8137dc619c16 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ModelDialog.tsx`**

- 源码声明的类型、组件或调用边界：`FormItem`, `ModelDraft`, `ModelProtocol`, `ConnectionFailure`, `FETCH_REASON_KEYS`, `getPresetStatusKey`, `getModelFetchKey`, `ModelDialog`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import type { ModelEntry, VendorFetchModelsResult, VendorPreset, VendorPresetMap } from '../../../..`；`import { Button } from '../../../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ModelDialog.tsx#L1-L640)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ModelNameField.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3b346784e8c1b8a4dfc025713a2ad40fc829dcff0ec4dfa504b5a752dab619c8 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ModelNameField.tsx`**

- 源码声明的类型、组件或调用边界：`ModelMenuPosition`, `ModelNameField`, `listboxId`, `rootRef`, `inputRef`, `menuRef`, `wasFetching`, `updateMenuPosition`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import { Check, ChevronDown, RefreshCw } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ModelNameField.tsx#L1-L308)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ModelProviderSelect.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f34c87b37e5e18c0bda4b7addc813276b90f280c2eca73d78743af400e487a71 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ModelProviderSelect.tsx`**

- 源码声明的类型、组件或调用边界：`ModelProtocol`, `ProviderOption`, `ProviderMenuPosition`, `getPresetApiAddress`, `GROUPS`, `VENDOR_TRANSLATION_KEYS`, `getVendorLabel`, `translationKey`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import { Check, ChevronDown, Search } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ModelProviderSelect.tsx#L1-L356)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ModelsSettings.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=94572e9cd698f974637e469fc982ba4ceab7e92150792fd4f3b1a688260d100c -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ModelsSettings.tsx`**

- 源码声明的类型、组件或调用边界：`EMPTY_VENDOR_CATALOG`, `ModelConfirmation`, `ValidationToast`, `ReplaceModelsResult`, `SaveModelsOptions`, `modelIdentity`, `parseModelsPayload`, `models`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { Check, ChevronRight } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import type { ModelEntry, VendorPresetMap } from '../../../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/ModelsSettings.tsx#L1-L568)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/OpenAIAccountField.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6d1972a1ee7f9551746e76d6dfe289df250f0bb60d634d9720e0902b9832db59 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/OpenAIAccountField.tsx`**

- 源码声明的类型、组件或调用边界：`SettingsRequest`, `LOGIN_POLL_MINIMUM_MS`, `AUTH_REQUEST_TIMEOUT_MS`, `MODEL_REQUEST_TIMEOUT_MS`, `LOGIN_START_TIMEOUT_MS`, `AuthStatus`, `LoginPayload`, `PendingLoginPayload`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { Copy, ExternalLink, KeyRound, LogOut } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import type { ModelEntry } from '../../../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/OpenAIAccountField.tsx#L1-L629)。
<!-- /kb:file -->
