---
title: "components-artifactspanel 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-artifactspanel 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/ooxmlArchiveLimits.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fa1a75c33532d54c96ca89d42dd6740cb24a3976d709973f32d1a4b3e2d0afea -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/ooxmlArchiveLimits.ts`**

- 源码声明的类型、组件或调用边界：`MEBIBYTE`, `END_OF_CENTRAL_DIRECTORY_SIGNATURE`, `ZIP64_END_OF_CENTRAL_DIRECTORY_SIGNATURE`, `ZIP64_END_OF_CENTRAL_DIRECTORY_LOCATOR_SIGNATURE`, `CENTRAL_DIRECTORY_ENTRY_SIGNATURE`, `ZIP64_EXTRA_FIELD_ID`, `MAX_ZIP_COMMENT_BYTES`, `OoxmlArchiveLimits`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/ooxmlArchiveLimits.ts#L1-L187)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/pptxPresentationParser.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8046ea7de1085b3ad0cecd54e71b864ec2ab0329478063fe8e8026123de6eedc -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/pptxPresentationParser.ts`**

- 源码声明的类型、组件或调用边界：`PresentationBounds`, `PresentationChart`, `PresentationColor`, `PresentationData`, `PresentationFill`, `PresentationImage`, `PresentationNode`, `PresentationParagraph`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import JSZip from 'jszip';`；`import { SaxesParser } from 'saxes';`；`import { OoxmlArchiveLimitError, PRESENTATION_ARCHIVE_LIMITS, inspectOoxmlArchive, isOoxmlArchiveLim`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/pptxPresentationParser.ts#L1-L1118)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/pptxPreview.worker.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9c078765f7dc265c46860ab3871461bf4099704b1aef1ceda707643933ee0272 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/pptxPreview.worker.ts`**

- 源码声明的类型、组件或调用边界：`workerScope`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { parsePresentation } from './pptxPresentationParser';`；`import { isOoxmlArchiveLimitError } from './ooxmlArchiveLimits';`；`import type { PresentationWorkerRequest, PresentationWorkerResponse } from './pptxPreviewModel';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/pptxPreview.worker.ts#L1-L21)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/pptxPreviewModel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=39ba1c6a1c957875307368d8584ad16b3ca8a549dbd397de30209dd9ce268396 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/pptxPreviewModel.ts`**

- 源码声明的类型、组件或调用边界：`MAX_PRESENTATION_PREVIEW_BYTES`, `MAX_PRESENTATION_UNCOMPRESSED_BYTES`, `PresentationColor`, `PresentationFill`, `PresentationStroke`, `PresentationSpacing`, `presentationLineHeight`, `PresentationRun`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { PRESENTATION_ARCHIVE_LIMITS } from './ooxmlArchiveLimits';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/pptxPreviewModel.ts#L1-L137)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/spreadsheetPreview.worker.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a888424bb563469dca12ded60b7dbc9bec5b05c52090ff1714e81f1e1a86a5c5 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/spreadsheetPreview.worker.ts`**

- 源码声明的类型、组件或调用边界：`workerScope`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { parseSpreadsheetWorkbook } from './spreadsheetWorkbookParser';`；`import { isOoxmlArchiveLimitError } from './ooxmlArchiveLimits';`；`import type { SpreadsheetWorkerRequest, SpreadsheetWorkerResponse } from './spreadsheetPreviewModel'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/spreadsheetPreview.worker.ts#L1-L23)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/spreadsheetPreviewModel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bb1c8e1c1ab5d3d07129b22ecc932db85fa75ed6a1c8da3a3c2464d780d12407 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/spreadsheetPreviewModel.ts`**

- 源码声明的类型、组件或调用边界：`MAX_SPREADSHEET_PREVIEW_BYTES`, `SpreadsheetCssValue`, `SpreadsheetCellStyle`, `SpreadsheetCellData`, `SpreadsheetRowData`, `SpreadsheetAxisSize`, `SpreadsheetMergeRange`, `SpreadsheetCellComment`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { SPREADSHEET_ARCHIVE_LIMITS } from './ooxmlArchiveLimits';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/spreadsheetPreviewModel.ts#L1-L191)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/spreadsheetWorkbookParser.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b459efcfd1156f0da09e6e60d879027587b8f4c687c98bb005b62ff5ce5537a0 -->
**`jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/spreadsheetWorkbookParser.ts`**

- 源码声明的类型、组件或调用边界：`Border`, `SaxesTagNS`, `SpreadsheetCellData`, `SpreadsheetCellStyle`, `SpreadsheetChart`, `SpreadsheetChartSeries`, `SpreadsheetDrawingAnchor`, `SpreadsheetImage`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import ExcelJS, { type Border, type Cell, type Color, type Fill, type Font, type Style, type Workboo`；`import JSZip from 'jszip';`；`import { SaxesParser, type SaxesTagNS } from 'saxes';`；`import SSF from 'ssf';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ArtifactsPanel/spreadsheetWorkbookParser.ts#L1-L1115)。
<!-- /kb:file -->
