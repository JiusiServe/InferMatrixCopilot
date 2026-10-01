---
title: "content 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# content 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/Annotator.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eda2a109eada75d62d1d50d21fc9d331e02acd53666c85568b6394b9a0130075 -->
**`jiuwenswarm/channels/browser/frontend/src/content/Annotator.ts`**

- 源码声明的类型、组件或调用边界：`TRANSIENT_CLASS`, `STYLE_ID`, `startAnnotator`, `action`, `m`, `_applyTransient`, `walker`, `node`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { MSG } from "@shared/constants";`；`import { HighlightMsg } from "@shared/types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/Annotator.ts#L1-L78)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/Extractor.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b492fd5787aa4864b991214e60203cb96b6ed720bddfff22bedeb58850510ef7 -->
**`jiuwenswarm/channels/browser/frontend/src/content/Extractor.ts`**

- 源码声明的类型、组件或调用边界：`extractPageContext`, `url`, `pageType`, `capturedAt`, `title`, `text`, `originalLength`, `truncateAtParagraphBoundary`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Readability } from "@mozilla/readability";`；`import { PageContext } from "@shared/types";`；`import { MAX_CONTEXT_CHARS } from "@shared/constants";`；`import { detectPageType } from "./PageTypeDetector";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/Extractor.ts#L1-L140)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/FormAssist.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3099680604930a3b16c5fe5b567f1613f71c8f7e62b142f46d52a3b6aceba235 -->
**`jiuwenswarm/channels/browser/frontend/src/content/FormAssist.ts`**

- 源码声明的类型、组件或调用边界：`startFormAssist`, `fillForm`, `input`, `nativeInputValueSetter`, `findInput`, `byId`, `byName`, `label`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { MSG } from "@shared/constants";`；`import { FillFormMsg } from "@shared/types";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/FormAssist.ts#L1-L67)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/PageTypeDetector.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4957d72cfafd288b31a153785374a657c7d955b5452c6f930f18901144b51709 -->
**`jiuwenswarm/channels/browser/frontend/src/content/PageTypeDetector.ts`**

- 源码声明的类型、组件或调用边界：`PageType`, `detectPageType`, `ogType`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/PageTypeDetector.ts#L1-L68)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/SelectionMonitor.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9b92fe39873b3d219899d1788565421a0e82b68beb8895579bdfc333ab434419 -->
**`jiuwenswarm/channels/browser/frontend/src/content/SelectionMonitor.ts`**

- 源码声明的类型、组件或调用边界：`_lastSelection`, `startSelectionMonitor`, `getLastSelection`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { MSG } from "@shared/constants";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/SelectionMonitor.ts#L1-L26)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/content/index.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6d00120e68713f91bef948893365f10a0e732ae4890218d822a8fb2b25a127ec -->
**`jiuwenswarm/channels/browser/frontend/src/content/index.ts`**

- 源码声明的类型、组件或调用边界：`log`, `el`, `pushContext`, `context`, `_lastUrl`, `_observer`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createLogger } from "@shared/logger";`；`import { MSG } from "@shared/constants";`；`import { extractPageContext } from "./Extractor";`；`import { startSelectionMonitor } from "./SelectionMonitor";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/content/index.ts#L1-L75)。
<!-- /kb:file -->
