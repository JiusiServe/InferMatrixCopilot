---
title: "features-settings 源码接口与集成边界 03"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-settings 源码接口与集成边界 03

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/components/ChannelListSection.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0d3d5ea706881af77e9019943414597ab4777ea6d73b7ddc7a39e2dcd6b8e05a -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/components/ChannelListSection.tsx`**

- 源码声明的类型、组件或调用边界：`ChannelGuideLanguage`, `EnableIcon`, `DisableIcon`, `EditIcon`, `ChannelListSectionProps`, `ChannelListSection`, `guideLanguage`, `label`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Unlink } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import { settingsActionIcons } from '../../../../../assets/settings';`；`import { Button, Tag } from '../../../../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/components/ChannelListSection.tsx#L1-L220)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/components/ChannelLogo.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=37bfd255c5645d996c4fd6ca0261eb84d1289f545383827bac4259eef894ace0 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/components/ChannelLogo.tsx`**

- 源码声明的类型、组件或调用边界：`ChannelLogo`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { getSettingsChannelLogo } from '../channelCatalog';`；`import type { SettingsChannelId } from '../channelTypes';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/components/ChannelLogo.tsx#L1-L22)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/components/XiaoyiEnableConfirmDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=00401ac9820797c3e495cd41132e5f9b9c512e81ec97f9bfab0d0bc4dd259a51 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/components/XiaoyiEnableConfirmDialog.tsx`**

- 源码声明的类型、组件或调用边界：`XiaoyiEnableConfirmDialog`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import { SettingsConfirmDialog } from '../../../components';`；`import type { useSettingsChannelsController } from '../useSettingsChannelsController';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/components/XiaoyiEnableConfirmDialog.tsx#L1-L27)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/definition.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b757f1eac8ec613cec2cb1c4a8ab322771afbff399f8e64b3abb593f369b4568 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/definition.ts`**

- 源码声明的类型、组件或调用边界：`channelsModule`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { settingsNavigationIcons } from '../../../../assets/settings';`；`import type { SettingsModuleDefinition } from '../../registry/types';`；`import { ChannelsModule } from './ChannelsModule';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/definition.ts#L1-L16)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/forms/FeishuChannelForm.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ac98562da2b5d5181688423fcebc56e8f920df32e30f1b538b1f2f40b090f592 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/forms/FeishuChannelForm.tsx`**

- 源码声明的类型、组件或调用边界：`FeishuChannelFormHandle`, `FeishuAppFormProps`, `FeishuAppForm`, `form`, `rules`, `items`, `FeishuChannelForm`, `FeishuChannelForm`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { forwardRef, useEffect, useImperativeHandle, useMemo } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Form, useForm, useFormValue } from '../../../../../components/form';`；`import { createFeishuAppFormItems } from '../channelFormItems';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/forms/FeishuChannelForm.tsx#L1-L71)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/forms/SimpleChannelForms.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6f049307f5ec2f3e8cb9a18c6d8783998a6a5d4955aa203c93d9ac9856b37931 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/forms/SimpleChannelForms.tsx`**

- 源码声明的类型、组件或调用边界：`DingtalkChannelForm`, `items`, `rules`, `TelegramChannelForm`, `items`, `rules`, `DiscordChannelForm`, `items`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import {`；`import { createChannelFormRules } from '../channelRequirements';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/forms/SimpleChannelForms.tsx#L1-L58)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/forms/StandardChannelForm.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f0abebbeaa2984593d4bd72341ef8ecc7de68db37999f1edc2e407d7fded542d -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/forms/StandardChannelForm.tsx`**

- 源码声明的类型、组件或调用边界：`StandardChannelForm`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Form } from '../../../../../components/form';`；`import type { FormItem, FormRules, FormValues } from '../../../../../components/form';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/forms/StandardChannelForm.tsx#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/forms/XiaoyiChannelForm.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6084a863f4009f5bea5e928f253a920463238145329a0696afa61c05c047b45a -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/forms/XiaoyiChannelForm.tsx`**

- 源码声明的类型、组件或调用边界：`XiaoyiChannelForm`, `enabled`, `apiId`, `items`, `rules`, `showApiIdHint`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo, useState } from 'react';`；`import { X } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import { useFormValue } from '../../../../../components/form';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/forms/XiaoyiChannelForm.tsx#L1-L43)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/useChannelForm.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c508575716c31f0a9d9595573e4872dcc0950f01b989d762cb551145ccdd5af2 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/useChannelForm.ts`**

- 源码声明的类型、组件或调用边界：`ChannelFormOptions`, `ChannelFormController`, `useChannelForm`, `form`, `formState`, `load`, `payload`, `persistPayload`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useState } from 'react';`；`import { useForm, useFormState } from '../../../../components/form';`；`import type { FormStore } from '../../../../components/form/core/FormStore';`；`import type { FormValues } from '../../../../components/form/types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/useChannelForm.ts#L1-L136)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/useSettingsChannelsController.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aff54c74ce82a0525ffd2918cbab2899ce39c2cf2ffb5fcd65fa56904090a158 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/useSettingsChannelsController.ts`**

- 源码声明的类型、组件或调用边界：`useSettingsChannelsController`, `loadChannels`, `payload`, `xiaoyi`, `feishu`, `dingtalk`, `telegram`, `discord`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { useFormValue } from '../../../../components/form';`；`import { deepEqual } from '../../../../components/form/core/FormStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/channels/useSettingsChannelsController.ts#L1-L415)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/experimental/ExperimentalSettings.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=29613b3ec6153d53c16f92d4f14c32633cf5376621183d7e28c6283c81d4ed8a -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/experimental/ExperimentalSettings.tsx`**

- 源码声明的类型、组件或调用边界：`ExternalCliAgentKind`, `ExternalCliConfigSaveResult`, `ExternalCliPendingChoice`, `CLI_DEFAULTS`, `NOTICE_AUTO_DISMISS_MS`, `externalCliReplayInFlight`, `ProactiveLimitsDialog`, `form`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useMemo, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { settingsActionIcons } from '../../../../assets/settings';`；`import { Button, Switch } from '../../../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/experimental/ExperimentalSettings.tsx#L1-L838)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/settings/modules/experimental/VideoDuplexModelSettings.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=43bfe4874aba54f26d00a8dfc49666339776c21a48120d3bd32df627e6037ee8 -->
**`jiuwenswarm/channels/web/frontend/src/features/settings/modules/experimental/VideoDuplexModelSettings.tsx`**

- 源码声明的类型、组件或调用边界：`Provider`, `VoiceProtocol`, `ReplyLanguage`, `SettingsValues`, `DEFAULTS`, `SECRET_KEYS`, `Payload`, `secretPlaceholder`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { settingsActionIcons } from '../../../../assets/settings';`；`import { Button, Select } from '../../../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/settings/modules/experimental/VideoDuplexModelSettings.tsx#L1-L360)。
<!-- /kb:file -->
