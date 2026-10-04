---
title: "channels-web 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# channels-web 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/A2UIErrorBoundary.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e82cd278e1c07943321e256baaf5b08cb64e9c463a217ad904cf7fbf965447cf -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/A2UIErrorBoundary.tsx`**

- 源码声明的类型、组件或调用边界：`ErrorInfo`, `A2UIErrorBoundaryProps`, `A2UIErrorBoundaryState`, `A2UIErrorBoundary`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Component, type ErrorInfo, type ReactNode } from 'react';`；`import { a2uiError } from './formDefaults';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/A2UIErrorBoundary.tsx#L1-L53)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/A2UIMessageContent.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=65fef2120cd38e01e8014a13bb261c1b9583bed7f900c2439a3c22d52a546e8b -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/A2UIMessageContent.tsx`**

- 源码声明的类型、组件或调用边界：`A2UIContentPart`, `A2UIMessageContentProps`, `RenderPart`, `safeNamespace`, `stableHash`, `hash`, `index`, `A2UIMessageContent`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useMemo, memo } from 'react';`；`import { useA2UIActions } from '@a2ui/react';`；`import { useTranslation } from 'react-i18next';`；`import { MarkdownRenderer } from '../../components/MarkdownRenderer';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/A2UIMessageContent.tsx#L1-L211)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/CheckBoxWithDefaults.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5310897a376b7667513633f9ed6511372c03d0459657d6a75f08a43c4678c2ad -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/CheckBoxWithDefaults.tsx`**

- 源码声明的类型、组件或调用边界：`A2UIComponentProps`, `AnyComponentNode`, `CheckBoxNodeLike`, `CheckBoxWithDefaults`, `props`, `id`, `label`, `readBoolean`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useId } from 'react';`；`import type { ChangeEvent } from 'react';`；`import {`；`import { hostWeightStyle, useA2UIBoundValue } from './fieldBinding';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/CheckBoxWithDefaults.tsx#L1-L70)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/DateTimeInputWithDefaults.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=916b482a957478f06391d1d6da5e579ee8e4a61c09b24bc1b21749993e4386b8 -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/DateTimeInputWithDefaults.tsx`**

- 源码声明的类型、组件或调用边界：`A2UIComponentProps`, `AnyComponentNode`, `DateTimeInputNodeLike`, `DateInputKind`, `dateInputKind`, `dateInputLabel`, `DateTimeInputWithDefaults`, `props`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useId } from 'react';`；`import type { ChangeEvent } from 'react';`；`import {`；`import { hostWeightStyle, useA2UIBoundValue } from './fieldBinding';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/DateTimeInputWithDefaults.tsx#L1-L77)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/MultipleChoiceWithDefaults.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9f82cf4b466ab11d7b6af7025b0f436d6fd9e49be5e6105d7d85485f4fe78334 -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/MultipleChoiceWithDefaults.tsx`**

- 源码声明的类型、组件或调用边界：`A2UIComponentProps`, `AnyComponentNode`, `DataValue`, `MultipleChoiceNodeLike`, `choiceValueToString`, `nonEmptyChoiceValue`, `text`, `selectedValuesFromData`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useId, useMemo, useState } from 'react';`；`import type { CSSProperties, ChangeEvent } from 'react';`；`import {`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/MultipleChoiceWithDefaults.tsx#L1-L288)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/SliderWithDefaults.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fc28fd372cad67dd193ddd5e19ab59fc98d7d9412b65d7094e4e58465e2a68f7 -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/SliderWithDefaults.tsx`**

- 源码声明的类型、组件或调用边界：`A2UIComponentProps`, `AnyComponentNode`, `SliderNodeLike`, `numberFromModel`, `SliderWithDefaults`, `props`, `id`, `minValue`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useId } from 'react';`；`import type { ChangeEvent } from 'react';`；`import {`；`import { hostWeightStyle, useA2UIBoundValue } from './fieldBinding';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/SliderWithDefaults.tsx#L1-L79)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/TextFieldWithDefaults.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=522f6d591ce27831f92c957472bdc3f498c33578a259a731181060c5dcf025f4 -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/TextFieldWithDefaults.tsx`**

- 源码声明的类型、组件或调用边界：`A2UIComponentProps`, `AnyComponentNode`, `TextFieldNodeLike`, `TextControlKind`, `textControlKind`, `extraProps`, `htmlInputType`, `TextFieldWithDefaults`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useId, useState } from 'react';`；`import type { ChangeEvent, HTMLInputTypeAttribute } from 'react';`；`import {`；`import { hostWeightStyle, useA2UIBoundValue } from './fieldBinding';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/TextFieldWithDefaults.tsx#L1-L100)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/TextWithDefaults.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f4064117a149e009c8509896de4daa200e5988c35b289316d74900b10588c7ba -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/TextWithDefaults.tsx`**

- 源码声明的类型、组件或调用边界：`A2UIComponentProps`, `AnyComponentNode`, `TextNodeLike`, `TextUsageHint`, `ClassMap`, `textClassMap`, `TextWithDefaults`, `props`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo } from 'react';`；`import type { CSSProperties } from 'react';`；`import ReactMarkdown from 'react-markdown';`；`import remarkGfm from 'remark-gfm';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/TextWithDefaults.tsx#L1-L68)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/a2uiContent.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9c10da17647b332f327610122a48db0e9cea55c8bd392d003d793f40392add36 -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/a2uiContent.ts`**

- 源码声明的类型、组件或调用边界：`A2UI_PROTOCOL_VERSION`, `A2UI_OPEN_TAG`, `A2UI_CLOSE_TAG`, `A2UI_MESSAGE_KEYS`, `A2UIProtocolVersion`, `A2UIContentPart`, `ParseA2UIContentOptions`, `DEFAULT_PENDING_TEXT`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ServerToClientMessage } from '@a2ui/react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/a2uiContent.ts#L1-L384)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/actionBridge.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ec7e8d6a6a145737354b34cda64c205ab356c57eb7dab1024b1d2b18afdb4a60 -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/actionBridge.ts`**

- 源码声明的类型、组件或调用边界：`A2UIClientEventContent`, `A2UIActionHandler`, `currentHandler`, `inFlightActionKeys`, `inFlightActionKey`, `userAction`, `surfaceId`, `sourceComponentId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { A2UIClientEventMessage } from '@a2ui/react';`；`import { isA2UIFeatureEnabled } from './featureConfig';`；`import { A2UI_PROTOCOL_VERSION } from './a2uiContent';`；`import { enrichA2UIClientEventWithDefaults } from './actionDefaults';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/actionBridge.ts#L1-L199)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/actionDefaults.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=af501a375eabfa906b42b9005d2f8cb97173753f2a406c5149a02ddb457fb440 -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/actionDefaults.ts`**

- 源码声明的类型、组件或调用边界：`UnknownRecord`, `ActionDefaultEntry`, `actionDefaults`, `surfaceDefaultsByPath`, `componentType`, `componentProps`, `type`, `actionName`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { A2UIClientEventMessage, ServerToClientMessage } from '@a2ui/react';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/actionDefaults.ts#L1-L226)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/featureConfig.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f234256a917290f8f1de26315c8bc5372feb43f58f8a29c1babe2bc80d46eeec -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/featureConfig.ts`**

- 源码声明的类型、组件或调用边界：`a2uiFeatureEnabled`, `a2uiFeatureListeners`, `setA2UIFeatureEnabled`, `isA2UIFeatureEnabled`, `subscribeA2UIFeatureEnabled`, `useA2UIFeatureEnabled`, `normalizeA2UIEnabled`, `text`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useSyncExternalStore } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/featureConfig.ts#L1-L43)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/fieldBinding.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e03264a93ee06ecb643f56455bd02406a0d8c25f61017f8227d822d019b69112 -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/fieldBinding.ts`**

- 源码声明的类型、组件或调用边界：`ReadModelValue`, `WriteModelValue`, `BoundValueOptions`, `alwaysSeedInitial`, `hostWeightStyle`, `useA2UIBoundValue`, `shouldSeed`, `storedValue`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useState } from 'react';`；`import type { CSSProperties } from 'react';`；`import type { DataValue } from '@a2ui/react';`；`import { dualWriteA2UIValue } from './formDefaults';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/fieldBinding.ts#L1-L72)。
<!-- /kb:file -->
