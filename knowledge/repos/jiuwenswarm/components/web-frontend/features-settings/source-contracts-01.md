---
title: "features-settings 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-settings 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/SettingsPage.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=451c0edaf33d49e36a855367a230ffc4e0bf1195b6d57b8f70be5452b993d2ad -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/SettingsPage.tsx`**

- 源码声明的类型、组件或调用边界：`SettingsPage`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { WebConnectionState } from '../../types';`；`import type { SettingsRequest } from './services/settingsContract';`；`import type {`；`import type { ExternalCliInstallStatuses } from '../../components/ExternalCliInstallDialog';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/SettingsPage.tsx#L1-L79)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/SettingsPageLayout.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=867ba80eb2360bdc3783f150110b8e5e026d160c064e1b1d04170c028b873418 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/SettingsPageLayout.tsx`**

- 源码声明的类型、组件或调用边界：`visibleItems`, `moduleAccess`, `sections`, `sectionAccess`, `items`, `SettingsItem`, `readOnly`, `readOnlyReason`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useMemo, useState, useSyncExternalStore } from 'react';`；`import { Check, CircleAlert } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import { Loading } from '../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/SettingsPageLayout.tsx#L1-L207)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/components/SettingItemRenderer.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5a6ebfbbd3fe00dfdea0d02bd7a2f3fd9a3ec9b84fc9e86b996841f101af6bbc -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/components/SettingItemRenderer.tsx`**

- 源码声明的类型、组件或调用边界：`EditingChange`, `settingFieldKey`, `InlineSettingInput`, `source`, `value`, `saving`, `hasChanges`, `cancel`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Button, Input, Select, Switch } from '../../../components/ui';`；`import type { SettingItemDefinition } from '../registry/types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/components/SettingItemRenderer.tsx#L1-L203)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/components/SettingRow.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5443e8ecf3876ab2ff51fddec90d4953218898bb066d472bf7fdbb988874d462 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/components/SettingRow.tsx`**

- 源码声明的类型、组件或调用边界：`SettingRow`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`；`import './SettingRow.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/components/SettingRow.tsx#L1-L38)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/components/SettingsConfirmDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4418e2a53f3aa69992f199202452e9b3a4cb8e433e7e46b96e5a5d0360e788a7 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/components/SettingsConfirmDialog.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `ButtonProps`, `SettingsConfirmDialogProps`, `SettingsConfirmDialog`, `titleId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useId, type ReactNode } from 'react';`；`import { X } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import { Button, Dialog, type ButtonProps } from '../../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/components/SettingsConfirmDialog.tsx#L1-L72)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/components/SettingsSection.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=19f9bfe0921439176e6eeb7f713265136bc9b51b37a723614beedf20fe504514 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/components/SettingsSection.tsx`**

- 源码声明的类型、组件或调用边界：`SettingsSection`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`；`import './SettingsSection.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/components/SettingsSection.tsx#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/AgentSettings.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=805bf0709151c60889b74c370d14f89780fd2f9fecc019d665de79760baf9838 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/AgentSettings.tsx`**

- 源码声明的类型、组件或调用边界：`FormItem`, `FormRules`, `MediaCapabilityModality`, `keyFields`, `modalities`, `videoGenFields`, `videoGenContextWindowField`, `visualGenFields`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { settingsActionIcons } from '../../../../assets/settings';`；`import { Button, Switch } from '../../../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/AgentSettings.tsx#L1-L618)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/GenerationModelConfigDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ed3e4b1ad7b7369d9b1f0589b86320ada7d1297bfe1ab00530f521677fa3e0aa -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/GenerationModelConfigDialog.tsx`**

- 源码声明的类型、组件或调用边界：`FormItem`, `GenerationSlot`, `EMPTY_VENDOR_CATALOG`, `OPENAI_PROTOCOL`, `SaveConfig`, `GenerationDraft`, `readConfig`, `trimSlash`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import type { VendorPreset, VendorPresetMap } from '../../../../types';`；`import { Button } from '../../../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/GenerationModelConfigDialog.tsx#L1-L462)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/MediaModelConfigDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=650122dc5862726461d37a0783c7ae0ab4546a6e5962ccaae36298103ed782f6 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/MediaModelConfigDialog.tsx`**

- 源码声明的类型、组件或调用边界：`FormItem`, `MediaModelDraft`, `EMPTY_VENDOR_CATALOG`, `FETCH_REASON_KEYS`, `SaveConfig`, `getPresetStatusKey`, `getModelFetchKey`, `validateMediaModelDraft`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import type { VendorFetchModelsResult, VendorPreset, VendorPresetMap } from '../../../../types';`；`import { Button } from '../../../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/MediaModelConfigDialog.tsx#L1-L517)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/definition.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=867b9ffe42aa381a79c546d95a72b193fe8661fdc249924cfb2addb23aa727a5 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/definition.ts`**

- 源码声明的类型、组件或调用边界：`agentModule`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { settingsNavigationIcons } from '../../../../assets/settings';`；`import type { SettingsModuleDefinition } from '../../registry/types';`；`import { AgentMediaSettings, AgentSearchSettings, VideoGenSettings, VisualGenSettings } from './Agen`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/definition.ts#L1-L43)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/generationModels.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0366f02c9343a888a5d893165a226553e2cd8a6697a6ca05f9d08c91968c1a64 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/generationModels.ts`**

- 源码声明的类型、组件或调用边界：`GenerationSlot`, `GenerationModel`, `MINIMAX_PROTOCOL`, `MODELARK_PROTOCOL`, `OPENROUTER_MODELS`, `MINIMAX_MODELS`, `MODELARK_MODELS`, `openRouterModelProtocol`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/generationModels.ts#L1-L211)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/mediaCapabilities.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8c4e027e7b0b174327aeb5a2cf500453c9110d25fd1b97b059061501838cbd89 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/mediaCapabilities.ts`**

- 源码声明的类型、组件或调用边界：`mediaCapabilityModalities`, `MediaCapabilityModality`, `mediaCapabilityConfigSuffixes`, `mediaCapabilityProviderMetadataSuffixes`, `mediaCapabilityConfigFields`, `mediaCapabilityProviderMetadataFields`, `mediaCapabilityContextWindowField`, `mediaCapabilityPersistenceFields`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/mediaCapabilities.ts#L1-L47)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/mediaModelConfig.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=becdfb5e10d62be57bc11b158d2bd1f136bfa2562ef6e169b4552f88a72f6f0e -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/mediaModelConfig.ts`**

- 源码声明的类型、组件或调用边界：`ModelInputMode`, `MediaCapabilityModality`, `MODEL_PLANS`, `MediaModelDraft`, `isModelPlan`, `readConfig`, `createMediaModelDraft`, `apiBase`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ModelPlan, VendorPresetMap } from '../../../../types';`；`import { normalizeContextWindowTokens, resolveDraftContextWindowTokens } from '../models/contextWind`；`import {`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/agent/mediaModelConfig.ts#L1-L92)。
<!-- /kb:file -->
