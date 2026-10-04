---
title: "features-settings 源码接口与集成边界 05"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-settings 源码接口与集成边界 05

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/contextWindow.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=25c5ee2b04326db58a500d79899771ef26b5492e5c593a5063ea90fef2d801f8 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/contextWindow.ts`**

- 源码声明的类型、组件或调用边界：`DEFAULT_CONTEXT_WINDOW_TOKENS`, `ONE_MILLION_CONTEXT_WINDOW_TOKENS`, `CONTEXT_WINDOW_PRESETS`, `MAX_CONTEXT_WINDOW_TOKENS`, `CONTEXT_WINDOW_PATTERN`, `CONTEXT_WINDOW_UNIT_MULTIPLIERS`, `parseContextWindowNumber`, `parseContextWindowTokens`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/contextWindow.ts#L1-L64)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/definition.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f9f5091543b96e1bf56345a49d00556451e1e18095cdb7cbf914b1c36b749261 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/definition.ts`**

- 源码声明的类型、组件或调用边界：`modelsModule`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { settingsNavigationIcons } from '../../../../assets/settings';`；`import type { SettingsModuleDefinition } from '../../registry/types';`；`import { FreeModelsSettings } from './FreeModelsSettings';`；`import { ModelsSettings } from './ModelsSettings';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/definition.ts#L1-L23)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/modelAdapters.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bc302ac14a72c19986661c9668f63a6d42915ff0b601c4438617ea67c1d1cb99 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/modelAdapters.ts`**

- 源码声明的类型、组件或调用边界：`ModelProtocol`, `ModelInputMode`, `CUSTOM_VENDOR_SELECTION`, `OPENAI_ACCOUNT_SELECTION`, `OPENAI_ACCOUNT_DEFAULT_API_BASE`, `ModelDraft`, `MODEL_DRAFT_FIELDS`, `rebaseModelDraft`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ModelEntry, ModelPlan, VendorPreset, VendorPresetMap } from '../../../../types';`；`import {`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/modelAdapters.ts#L1-L316)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/modelListOperations.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a2971fa5ae3d00076f8c1afcd6a8a6fc7fa5ebfd42e32e25a3fe3ae98fe0f492 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/modelListOperations.ts`**

- 源码声明的类型、组件或调用边界：`LOGIN_MODEL_SOURCE`, `ModelDisplayItem`, `ModelDisplayGroup`, `isRuntimeGrantedModel`, `getEditableModels`, `getModelDisplayGroups`, `editableGroups`, `items`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ModelEntry } from '../../../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/modelListOperations.ts#L1-L85)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/modelReasoning.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc56a8a1a0f21f089a5e617efba7ab1e8a74eaaf2b7ca8ec5574c5c61890bef1 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/modelReasoning.ts`**

- 源码声明的类型、组件或调用边界：`record`, `parseReasoningCapability`, `parseProtocols`, `protocols`, `parseRequiredProtocols`, `protocols`, `parseReasoningCapabilities`, `parseReasoningRules`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/modelReasoning.ts#L1-L126)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/modelValidation.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1039993c7daebf81c68634b77836c591d40b4710e57a28333811bf75f90ef6c1 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/modelValidation.ts`**

- 源码声明的类型、组件或调用边界：`ModelDraft`, `ModelDraftErrors`, `MAX_API_KEY_LENGTH`, `validateModelDraft`, `errors`, `alias`, `modelName`, `apiBase`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ModelEntry, VendorPresetMap } from '../../../../types';`；`import { parseContextWindowTokens } from './contextWindow';`；`import { CUSTOM_VENDOR_SELECTION, OPENAI_ACCOUNT_SELECTION, findVendorPreset, type ModelDraft } from`；`import { isReasoningLevelSupported, resolveModelReasoning } from './modelReasoning';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/models/modelValidation.ts#L1-L81)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/personalContext/PersonalContextSettingsModule.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=752308b3ce360ec4fa6ce4fa87aaa26af333967279286d3f550e5fc4e8371cd5 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/personalContext/PersonalContextSettingsModule.tsx`**

- 源码声明的类型、组件或调用边界：`PersonalContextSettingsModule`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useSettingsServices } from '../../services/SettingsServicesProvider';`；`import { FEATURE_PERSONAL_CONTEXT_UI } from '../../../../featureFlags';`；`import { PersonalContextSettingsPanel } from '../../../../components/PersonalContext/SettingsPanel';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/personalContext/PersonalContextSettingsModule.tsx#L1-L16)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/personalContext/definition.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c5b71d658c90fc890d3291e5f6f8151b6606abcaa3e21f376680c268da62fb8d -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/personalContext/definition.ts`**

- 源码声明的类型、组件或调用边界：`personalContextSettingsModule`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { settingsNavigationIcons } from '../../../../assets/settings';`；`import type { SettingsModuleDefinition } from '../../registry/types';`；`import { PersonalContextSettingsModule } from './PersonalContextSettingsModule';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/personalContext/definition.ts#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/registry/accessPolicy.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2bfe83a29b6e62643e282e57cbf64ad7552a16f94c2a874947279c50c5590f34 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/registry/accessPolicy.ts`**

- 源码声明的类型、组件或调用边界：`openSourceSettingsAccessPolicy`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { SettingsAccessPolicy } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/registry/accessPolicy.ts#L1-L10)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/registry/buildSettingsPageDefinition.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=af7691a1168905b2c4d3cb4e5566b63ec586e579148e26c71e2b3d8b96b9ad34 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/registry/buildSettingsPageDefinition.ts`**

- 源码声明的类型、组件或调用边界：`ACCESS_LEVEL_RANK`, `assertNonEmpty`, `accessNodeKey`, `assertTargetExists`, `module`, `section`, `addModule`, `effectiveAnchorId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createSettingsPageDefinition } from './createSettingsPageDefinition';`；`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/registry/buildSettingsPageDefinition.ts#L1-L207)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/registry/createSettingsPageDefinition.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=04a217340501a4c137557a8b6812e921e53af3baf2c8cff6f6668396115b704b -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/registry/createSettingsPageDefinition.ts`**

- 源码声明的类型、组件或调用边界：`assertId`, `assertUnique`, `seen`, `id`, `settingItemI18nKey`, `flattenItems`, `validateItem`, `component`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { isSettingsSource, isSettingsSourceComponent, isSettingsSourceKey } from '../services/settin`；`import type { SettingItemDefinition, SettingsModuleDefinition, SettingsPageDefinition } from './type`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/registry/createSettingsPageDefinition.ts#L1-L128)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/registry/openSourceDefinition.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3432238b57be358cb1fb72695dc75426cb53bb97faf1edf9177fc4cd4d9a1179 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/registry/openSourceDefinition.ts`**

- 源码声明的类型、组件或调用边界：`openSourceSettingsPageDefinition`, `settingsPageDefinition`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createSettingsPageDefinition } from './createSettingsPageDefinition';`；`import { openSourceSettingsAccessPolicy } from './accessPolicy';`；`import { generalModule } from '../modules/general';`；`import { modelsModule } from '../modules/models';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/registry/openSourceDefinition.ts#L1-L28)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/registry/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f6aa488451dcd5a9efe0915d3b5b202bdc99707e631de61b87bf9c7a788a5ec -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/registry/types.ts`**

- 源码声明的类型、组件或调用边界：`I18nKey`, `SettingsModuleId`, `SettingsAccessLevel`, `SettingsCompositionMode`, `SettingsSource`, `SettingValue`, `SettingsAccessNode`, `SettingsAccessContext`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ComponentType, ElementType } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/registry/types.ts#L1-L101)。
<!-- /kb:file -->
