---
title: "hooks 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# hooks 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/hooks/useAdaptiveTooltip.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=22977b03bff1abd921faf8acc85d0491795e79b3c8fbffff2b38473fbd2e6dea -->
**`jiuwenswarm/channels/web/frontend/src/hooks/useAdaptiveTooltip.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `VIEWPORT_MARGIN`, `TOOLTIP_GAP`, `TooltipPlacement`, `TooltipAlign`, `TooltipState`, `TooltipHandlers`, `UseAdaptiveTooltipOptions`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useLayoutEffect, useRef, useState, type ReactNode, type RefObject }`；`import { createPortal } from 'react-dom';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useAdaptiveTooltip.tsx#L1-L218)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublication.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eae5f762ec548062c2a6fdf37dc39efc6c28a1f3d44e60cd9d644702e41861ab -->
**`jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublication.ts`**

- 源码声明的类型、组件或调用边界：`PublicationState`, `publicationKey`, `useAssetPublication`, `signature`, `refresh`, `cancelled`, `keys`, `valid`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { assetPublishApi } from '../services/assetPublishApi';`；`import { type PublicationState } from '../features/assetPublication';`；`import type { AssetReference } from '../types/assetPublish';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublication.ts#L1-L47)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a507fa68b500120aa12d7ec51fb3ad873676ceb871b39dad4992f88322081c95 -->
**`jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts`**

- 源码声明的类型、组件或调用边界：`PUBLISH_RESTORE_KEY`, `emptyMetadata`, `authScope`, `useAssetPublish`, `activeSubmission`, `updateSubmission`, `active`, `locked`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { webClient } from '../services/webClient';`；`import { useCallback, useEffect, useRef, useState } from 'react';`；`import { assetPublishApi } from '../services/assetPublishApi';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useAssetPublish.ts#L1-L286)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/hooks/useDesktopLocalFilePickerReady.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4eeafef2f0550175932d43fe4ded61eb683e79af6313772c76e2551032eac885 -->
**`jiuwenswarm/channels/web/frontend/src/hooks/useDesktopLocalFilePickerReady.ts`**

- 源码声明的类型、组件或调用边界：`useDesktopLocalFilePickerReady`, `markReady`, `onReady`, `intervalId`, `timeoutId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useDesktopLocalFilePickerReady.ts#L1-L53)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/hooks/useFullscreenPanel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=75cf4c4078aba3f753291c790609c64d3608c8347823c0d57f809b78b4a459ee -->
**`jiuwenswarm/channels/web/frontend/src/hooks/useFullscreenPanel.ts`**

- 源码声明的类型、组件或调用边界：`FullscreenPanelResult`, `useFullscreenPanel`, `ref`, `enter`, `el`, `exit`, `toggle`, `el`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useRef, useState } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useFullscreenPanel.ts#L1-L58)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/hooks/useHorizontalScrollEdges.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3c4079e405eb87370cabdd59b47ab48794d0d77f7742be528ab1428c38e63de1 -->
**`jiuwenswarm/channels/web/frontend/src/hooks/useHorizontalScrollEdges.ts`**

- 源码声明的类型、组件或调用边界：`HorizontalScrollEdgesResult`, `useHorizontalScrollEdges`, `ref`, `update`, `el`, `next`, `el`, `observer`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useLayoutEffect, useRef, useState } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useHorizontalScrollEdges.ts#L1-L37)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/hooks/useResponsive.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aee7a1f8b417ed9721b87f4389fdf3c00080ef069521bfd0898272d355852ac7 -->
**`jiuwenswarm/channels/web/frontend/src/hooks/useResponsive.ts`**

- 源码声明的类型、组件或调用边界：`RefObject`, `BreakpointKey`, `useMediaQuery`, `mql`, `handler`, `useMaxWidth`, `useMinWidth`, `useResponsiveLayout`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useLayoutEffect, useRef, useState, type RefObject } from 'react';`；`import { breakpoints, canFitBoth, canFitToolPanelOnly, type BreakpointKey } from '../styles/breakpoi`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useResponsive.ts#L1-L202)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/hooks/useSpeech.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1e201a37afb83bd16cb58d6397a5d7dd013f52230475472f531de053c497b508 -->
**`jiuwenswarm/channels/web/frontend/src/hooks/useSpeech.ts`**

- 源码声明的类型、组件或调用边界：`UseSpeechRecognitionOptions`, `UseSpeechRecognitionReturn`, `SpeechRecognitionEventMap`, `SpeechRecognitionInstance`, `SpeechRecognitionConstructor`, `Window`, `SpeechRecognition`, `useSpeechRecognition`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState, useCallback, useRef, useEffect } from 'react';`；`import i18n from '../i18n';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/hooks/useSpeech.ts#L1-L392)。
<!-- /kb:file -->
