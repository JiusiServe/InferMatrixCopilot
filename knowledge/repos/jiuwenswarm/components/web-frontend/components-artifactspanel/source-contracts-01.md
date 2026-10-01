---
title: "components-artifactspanel 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-artifactspanel 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/ArtifactExpandedPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f9aa44d5f6c25e2a2d543ac8f5239b6370648ee13f0487c986e48c469c4b5d3a -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/ArtifactExpandedPanel.tsx`**

- 源码声明的类型、组件或调用边界：`ArtifactExpandedPanel`, `artifacts`, `selectedArtifact`, `selectedIndex`, `hasPrev`, `hasNext`, `handlePresentationStructureInvalidChange`, `next`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { useSessionArtifacts } from '.';`；`import { ArtifactList } from '.';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/ArtifactExpandedPanel.tsx#L1-L96)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/CodePreview.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8935606f680c9b86382588e8f36bd21597950420ebd3d789f3384891d59c965c -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/CodePreview.tsx`**

- 源码声明的类型、组件或调用边界：`lightPreviewTheme`, `LoadState`, `CodePreview`, `hostRef`, `disposed`, `view`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { defaultHighlightStyle, syntaxHighlighting } from '@codemirror/language';`；`import { EditorState } from '@codemirror/state';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/CodePreview.tsx#L1-L95)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/DocxPreview.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a1f10f60d9de43a87261b110c2b00a48b63e9adac9834a7870a9d56d0f7be34e -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/DocxPreview.tsx`**

- 源码声明的类型、组件或调用边界：`DocxPreviewState`, `DOCX_PAGE_CLASS`, `DocxPreview`, `bodyRef`, `styleRef`, `body`, `styleHost`, `abortController`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useRef, useState } from 'react';`；`import { LoaderCircle } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/DocxPreview.tsx#L1-L116)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/FilePreview.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c6a354c86f6a85a510064924a96e3b33c5541d186606071d0882050a1beaf4b0 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/FilePreview.tsx`**

- 源码声明的类型、组件或调用边界：`PreviewKind`, `PreviewArtifact`, `TextKind`, `Notice`, `TextPreview`, `url`, `cancelled`, `contentType`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { AlertCircle, LoaderCircle } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import { MarkdownRenderer } from '../MarkdownRenderer';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/FilePreview.tsx#L1-L161)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/PresentationPreview.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=58b8da6e65932afab5ec1b54261bef96d9f2fec46912199a22459209af4591c7 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/PresentationPreview.tsx`**

- 源码声明的类型、组件或调用边界：`CSSProperties`, `PresentationChart`, `PresentationData`, `PresentationFill`, `PresentationImage`, `PresentationNode`, `PresentationParagraph`, `PresentationShape`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState, type CSSProperties } from`；`import { AlertCircle, ChevronLeft, ChevronRight, LoaderCircle } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import clsx from 'clsx';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/PresentationPreview.tsx#L1-L934)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/SpreadsheetPreview.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0ad5cb13525cb02c2f38b1514f641039fa064997ef212ea394e25debd24474d0 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/SpreadsheetPreview.tsx`**

- 源码声明的类型、组件或调用边界：`CSSProperties`, `SpreadsheetCellData`, `SpreadsheetCellStyle`, `SpreadsheetChart`, `SpreadsheetDrawingAnchor`, `SpreadsheetMergeRange`, `SpreadsheetSheetData`, `SpreadsheetWorkerResponse`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useId, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent as Reac`；`import { AlertCircle, ChevronDown, LoaderCircle } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import clsx from 'clsx';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/SpreadsheetPreview.tsx#L1-L739)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d0ead7e889fa9269389b028c41de0fb3ca2d18df715b16bda1c52a785628a166 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts`**

- 源码声明的类型、组件或调用边界：`ArtifactItem`, `fileArtifactId`, `normalizeDownloadUrl`, `normalizedUrl`, `normalizedToken`, `preferArtifact`, `existingTs`, `candidateTs`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { FileDownloadItem, Message } from '../../types';`；`import { extractTokenFromDownloadUrl, getFileIdentityKey, resolveFilePath } from '../../utils/fileDo`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/artifactCollection.ts#L1-L119)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/chartGeometry.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8683307ba0bdb6412401dc0bd1fb8df0d22c855ba22316a4e8ad80f2db375089 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/chartGeometry.ts`**

- 源码声明的类型、组件或调用边界：`AxisSpan`, `CategoryBand`, `AxisDomain`, `ensureNonZeroAxisSpan`, `linearPosition`, `spanFromBaseline`, `categoryCenter`, `categoryPoint`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/chartGeometry.ts#L1-L79)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/codeLanguageExtensions.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3c614eba981623b15034395e680783bd301a7ae127ea5389e89a914676957716 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/codeLanguageExtensions.ts`**

- 源码声明的类型、组件或调用边界：`CODE_LANGUAGE_EXTENSIONS`, `CodeLanguageExtension`, `CODE_LANGUAGE_EXTENSION_SET`, `fileExtension`, `value`, `isCodeLanguageExtension`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/codeLanguageExtensions.ts#L1-L50)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/codeLanguages.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ecb17c21664fb2c3f64f9f78fa31543ea18b485046ca697761f6d6650ed2f410 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/codeLanguages.ts`**

- 源码声明的类型、组件或调用边界：`CodeLanguageExtension`, `LanguageLoader`, `javascript`, `cpp`, `LANGUAGE_LOADERS`, `loadCodeLanguage`, `extension`, `mime`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { Extension } from '@codemirror/state';`；`import { StreamLanguage } from '@codemirror/language';`；`import { fileExtension, isCodeLanguageExtension, type CodeLanguageExtension } from './codeLanguageEx`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/codeLanguages.ts#L1-L57)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8d5cc0d4b56cb215de1d613b2729a1d499b1519857175c8784db2d085a080071 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts`**

- 源码声明的类型、组件或调用边界：`PreviewFile`, `PreviewResource`, `TextKind`, `PreviewKind`, `TEXT_EXTENSIONS`, `IMAGE_MIME_TYPES`, `IMAGE_EXTENSIONS`, `inlineDownloadUrl`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { fileExtension, isCodeLanguageExtension } from './codeLanguageExtensions';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/filePreviewModel.ts#L1-L99)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3d7bd9186ef836fcc43a4a1d332872ab915b3a87ff9ce859c173b433810fad1b -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx`**

- 源码声明的类型、组件或调用边界：`DesktopSaveApiResult`, `ArtifactItem`, `DownloadCapableWindow`, `useSessionArtifacts`, `activeSessionId`, `messages`, `useSessionArtifactsCount`, `ArtifactList`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo } from 'react';`；`import { Download } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import clsx from 'clsx';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/index.tsx#L1-L121)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/officeFontStack.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8f7c49e06e6b49d209553e46a4cdc26679d7da1f972e09eac7f453e7b5da7023 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/officeFontStack.ts`**

- 源码声明的类型、组件或调用边界：`MICROSOFT_YAHEI`, `SIMSUN`, `CROSS_PLATFORM_FALLBACK_FONTS`, `officeFontStack`, `secondaryFonts`, `simSunIndex`, `declared`, `seen`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/officeFontStack.ts#L1-L54)。
<!-- /kb:file -->
