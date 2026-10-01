---
title: "components-markdownrenderer 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-markdownrenderer 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/MarkdownRenderer.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=26f23982533307486d1b58a3bf0e5d0efa9a4e1a17ebb9db28bcd46db93126c5 -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/MarkdownRenderer.tsx`**

- 源码声明的类型、组件或调用边界：`AnchorHTMLAttributes`, `MarkdownRendererProps`, `MarkdownContentLinesContext`, `MarkdownStreamingContext`, `MermaidCanvasMinHeightContext`, `MarkdownIncludeMathMLContext`, `MarkdownLinkClickContext`, `MarkdownLink`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createContext, useContext, useMemo, type AnchorHTMLAttributes, type HTMLAttributes } from '`；`import ReactMarkdown from 'react-markdown';`；`import type { Element as HastElement } from 'hast';`；`import { unescapeLiteralNewlines } from '../../utils/finalContent';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/MarkdownRenderer.tsx#L1-L121)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/codeBlocks/fencedCode.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9a3101ac798f6fc8e70e0dac1d7ce6a9eb7f68fb1f92957000f2342a12d626a2 -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/codeBlocks/fencedCode.ts`**

- 源码声明的类型、组件或调用边界：`HTMLAttributes`, `MarkdownPositionPoint`, `PositionedMarkdownNode`, `getCodeElement`, `childArray`, `child`, `getCodeLanguage`, `languageClass`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Children, isValidElement, type HTMLAttributes, type ReactElement, type ReactNode } from 're`；`import type { FencedCodeBlock } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/codeBlocks/fencedCode.ts#L1-L61)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/codeBlocks/registry.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2531e04c0369759d7f6c06fafe9f967863e09027ecc0e9434ff3494638e14026 -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/codeBlocks/registry.tsx`**

- 源码声明的类型、组件或调用边界：`MermaidCodeBlock`, `FENCED_CODE_ADAPTERS`, `ADAPTERS_BY_LANGUAGE`, `getFencedCodeAdapter`, `adapter`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { JSX } from 'react';`；`import { MermaidDiagram } from '../diagrams/MermaidDiagram';`；`import { SvgDiagram } from '../diagrams/SvgDiagram';`；`import type { FencedCodeAdapter, FencedCodeBlock, FencedCodeRendererProps } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/codeBlocks/registry.tsx#L1-L30)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/codeBlocks/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5424db5d3bbd27874065c734a25c0cef2a74a799eaf0882d345eddb75b4eb73c -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/codeBlocks/types.ts`**

- 源码声明的类型、组件或调用边界：`FencedCodeBlock`, `FencedCodeRendererProps`, `FencedCodeAdapter`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ComponentType } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/codeBlocks/types.ts#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/DiagramViewer.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d550c0a4a4a8643345394e962b3bbf7e8389f7f64c7a7f69e5878f3f678c1b40 -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/DiagramViewer.tsx`**

- 源码声明的类型、组件或调用边界：`HTMLAttributes`, `DiagramExportConfig`, `DiagramViewMode`, `DiagramToolbarAction`, `DiagramMenuItem`, `DiagramViewerProps`, `ToolbarButtonProps`, `ToolbarButton`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import clsx from 'clsx';`；`import { Copy, Ellipsis, ImageDown } from 'lucide-react';`；`import { useEffect, useRef, useState, type HTMLAttributes, type ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/DiagramViewer.tsx#L1-L216)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/MermaidDiagram.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=91b47ff8b4d5930c619b3f41b17d6bc8ccfe397b418170ac4b56226a2e742c25 -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/MermaidDiagram.tsx`**

- 源码声明的类型、组件或调用边界：`CSSProperties`, `DiagramToolbarAction`, `MermaidSvgRenderer`, `MermaidRenderState`, `MermaidDiagramProps`, `Point`, `MermaidSvgDimensions`, `normalizeMermaidSvgDimensions`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import clsx from 'clsx';`；`import { RotateCcw, ZoomIn, ZoomOut } from 'lucide-react';`；`import { useEffect, useId, useLayoutEffect, useRef, useState, type CSSProperties } from 'react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/MermaidDiagram.tsx#L1-L323)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/SvgDiagram.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9189104010879cb19061de28e920f9be772c874ec72fbeb2323042ead498d2f3 -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/SvgDiagram.tsx`**

- 源码声明的类型、组件或调用边界：`DiagramViewMode`, `SvgMarkupStatus`, `SvgDiagramProps`, `getStatusText`, `SvgDiagram`, `previewRef`, `preview`, `status`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useMemo, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { UNTRUSTED_STATIC_PREVIEW_SANDBOX } from '../isolatedPreview';`；`import { DiagramViewer, type DiagramViewMode } from './DiagramViewer';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/SvgDiagram.tsx#L1-L71)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/diagramExport.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a7e5e769e961e4a0faf97dd84eef38fec21aa3c102ad22f29ba41a06d8885076 -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/diagramExport.ts`**

- 源码声明的类型、组件或调用边界：`SVG_EXPORT_MAX_DIMENSION`, `SVG_EXPORT_MAX_AREA`, `loadSvgImage`, `blob`, `url`, `image`, `convertSvgToPng`, `image`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { getSvgNaturalHeight, getSvgNaturalWidth } from '../../../utils/svgDimensions';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/diagramExport.ts#L1-L52)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/mermaidLayout.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f5540699a284c5d1d5064e69479ac22f7a135453a6c208e3c42b1a8b0d9821da -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/mermaidLayout.ts`**

- 源码声明的类型、组件或调用边界：`MERMAID_CANVAS_MAX_HEIGHT`, `MERMAID_CANVAS_MIN_HEIGHT`, `MERMAID_CANVAS_MIN_DISPLAY_SCALE`, `MERMAID_CANVAS_TOP_OFFSET`, `MERMAID_CANVAS_BOTTOM_OFFSET`, `MermaidCanvasLayoutInput`, `MermaidCanvasLayout`, `clampMermaidScale`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/mermaidLayout.ts#L1-L56)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/mermaidRuntime.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bf5d7df5ba72cc426b055d6c5bef2850ef9b6f946769a41452ba0533b4c3ce2a -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/mermaidRuntime.ts`**

- 源码声明的类型、组件或调用边界：`MermaidRuntime`, `MermaidRuntimeLoader`, `MermaidSvgRenderer`, `MERMAID_CONFIG`, `createMermaidRenderer`, `runtimePromise`, `getRuntime`, `renderMermaidSvg`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { MermaidConfig } from 'mermaid';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/mermaidRuntime.ts#L1-L45)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/svgPreview.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c77daceb3685d1861ed329525b3aca71baff52da346437c03c1c4eb5465cc80d -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/svgPreview.ts`**

- 源码声明的类型、组件或调用边界：`SvgMarkupStatus`, `SvgPreview`, `SVG_NAMESPACE`, `SVG_PREVIEW_DOCUMENT`, `getSvgPreview`, `document`, `root`, `svg`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createStaticPreviewDocument } from '../isolatedPreview';`；`import { getSvgNaturalHeight, getSvgNaturalWidth } from '../../../utils/svgDimensions';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/svgPreview.ts#L1-L117)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/useDiagramExportActions.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=33db50ed6b8ec9d0aad7b62a6990d13800bbcaeba8541f3a70e34aa6a4083742 -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/useDiagramExportActions.ts`**

- 源码声明的类型、组件或调用边界：`DiagramExportConfig`, `DiagramExportActions`, `useDiagramExportActions`, `timeout`, `copyCode`, `downloadImage`, `image`, `outcome`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { convertSvgToPng, saveBlob } from './diagramExport';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/diagrams/useDiagramExportActions.ts#L1-L49)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/isolatedPreview.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d5148088ceb6a6a10fa7dc4cd5e49da1cbb50e132aa3e3abde854ae795b09c59 -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/isolatedPreview.ts`**

- 源码声明的类型、组件或调用边界：`UNTRUSTED_STATIC_PREVIEW_SANDBOX`, `UNTRUSTED_STATIC_PREVIEW_CSP`, `StaticPreviewDocumentOptions`, `createStaticPreviewDocument`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/isolatedPreview.ts#L1-L26)。
<!-- /kb:file -->
