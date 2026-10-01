---
title: "features-rsi 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-rsi 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/featureConfig.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7c67f57e4a6abe247f6da0fd0e11e4beb72ea8860ed96dc7bd0f98a900dfa4ff -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/featureConfig.ts`**

- 源码声明的类型、组件或调用边界：`rsiFeatureEnabled`, `rsiFeatureListeners`, `setRSIFeatureEnabled`, `isRSIFeatureEnabled`, `subscribeRSIFeatureEnabled`, `useRSIFeatureEnabled`, `normalizeRSIEnabled`, `text`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useSyncExternalStore } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/featureConfig.ts#L1-L33)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/latexPreview.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=228a64027552dc38ad67dfc9abbd77a40f0baad766d97cb7e47a677fbd45c600 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/latexPreview.ts`**

- 源码声明的类型、组件或调用边界：`LatexPreviewOptions`, `stripComments`, `findMatchingBrace`, `depth`, `i`, `ch`, `unwrapSizingCommands`, `pattern`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/latexPreview.ts#L1-L458)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/mockData.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9f487e30bbcaa92119dbe9aaeeba0b3daf1d3b947b36b5ba66196edb73a6d0de -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/mockData.ts`**

- 源码声明的类型、组件或调用边界：`LATENCY`, `delay`, `RSI_LOCAL_ARTIFACT_PATH`, `LOCAL_TEST_ARTIFACT_PATH`, `rsiMockModelList`, `mockTasks`, `buildMockTree`, `mk`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/mockData.ts#L1-L414)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/rsiApi.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b329ed36a9204134db7ce9e225e6e3b9456f4e75db30a177ede1b7fb2454a3a8 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/rsiApi.ts`**

- 源码声明的类型、组件或调用边界：`RSI_EVENTS`, `METHOD`, `RSI_MOCK_STORAGE_KEY`, `isMockEnabled`, `RSI_SESSION_STORAGE_KEY`, `inMemoryRsiSessionId`, `getRsiSessionId`, `stored`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { webRequest } from '../../services/webClient';`；`import { rsiMock } from './mockData';`；`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/rsiApi.ts#L1-L763)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/rsiArtifactFiles.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5c76311d1ba74bd769684f44425cf3c95af7459fc18df3393df314d4c9b2b905 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/rsiArtifactFiles.ts`**

- 源码声明的类型、组件或调用边界：`RsiArtifactSource`, `RsiArtifactFileEntry`, `RsiArtifactLoadResult`, `BINARY_EXTENSIONS`, `MIME_BY_EXTENSION`, `LATEX_TEXT_EXTENSIONS`, `normalizePath`, `relativePathFor`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { RsiArtifactFileGetResult, RsiTreeNode } from './types';`；`import { rsiArtifactFilesGet, rsiArtifactFilesList } from './rsiApi';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/rsiArtifactFiles.ts#L1-L167)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/rsiPresentation.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=effcf16f1472b380a86474369336b2c30e30eb50448bf91088b71651daad5ded -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/rsiPresentation.ts`**

- 源码声明的类型、组件或调用边界：`NodeStatusKind`, `nodeTypeToStatusKind`, `statusKindClass`, `legendDotClass`, `JsonRecord`, `asRecord`, `asText`, `text`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/rsiPresentation.ts#L1-L975)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/rsiStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=509707c59ae85ca0e15825efe8b21c52651a992a27821a141dc1709efe949ea3 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/rsiStore.ts`**

- 源码声明的类型、组件或调用边界：`RsiDetailState`, `RsiState`, `emptyDetail`, `detailRequests`, `useRsiStore`, `list`, `pending`, `request`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`；`import type {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/rsiStore.ts#L1-L326)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/rsiTreeLayout.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5a90eaae14dc76e115a886a36c875dc242b8032afa3f055968c55f47c4e6fc34 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/rsiTreeLayout.ts`**

- 源码声明的类型、组件或调用边界：`NodeRuntimeKind`, `LayoutNode`, `LayoutEdge`, `TreeLayout`, `NODE_W`, `NODE_H`, `DEPTH_GAP`, `SIBLING_GAP`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { RsiTreeNode } from './types';`；`import { nodeMetrics, nodeRuntimeKindForNode, type NodeRuntimeKind } from './rsiPresentation';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/rsiTreeLayout.ts#L1-L201)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c2490e3ca0d9e2a0d2504d4bc59d266e631391d39e820b79032fa0e7d5bfb025 -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/types.ts`**

- 源码声明的类型、组件或调用边界：`RsiScenario`, `RsiArtifactType`, `RsiTaskStatus`, `RsiNodeType`, `RsiUsage`, `RsiDatasetValidateParams`, `RsiDatasetValidateResult`, `RsiTaskCreateBase`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/types.ts#L1-L258)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/rsi/useRsiEvents.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fb18558d5848c17509e3fa0537913e710d32f8a2b34ec6d731b87a6efc41745a -->
**`jiuwenswarm/channels/web/frontend/src/features/rsi/useRsiEvents.ts`**

- 源码声明的类型、组件或调用边界：`useRsiEvents`, `applyStatusChanged`, `applyProgress`, `applyTreeDelta`, `offStatus`, `normalized`, `offProgress`, `normalized`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect } from 'react';`；`import { webClient } from '../../services/webClient';`；`import { useRsiStore } from './rsiStore';`；`import {`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/rsi/useRsiEvents.ts#L1-L42)。
<!-- /kb:file -->
