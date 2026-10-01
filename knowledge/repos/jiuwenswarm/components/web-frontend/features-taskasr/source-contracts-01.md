---
title: "features-taskasr 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-taskasr 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/taskAsr/featureFlag.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cfe8c99ff675017649964bbb23ac5c646736e26212ae101db83f3ed734df87ec -->
**`jiuwenswarm/channels/web/frontend/src/features/taskAsr/featureFlag.ts`**

- 源码声明的类型、组件或调用边界：`enabled`, `listeners`, `setTaskAsrEnabled`, `useTaskAsrEnabled`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useSyncExternalStore } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/featureFlag.ts#L1-L21)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2a7e5a4de677c12c0d6826bb06af4fd74a02bf68b1653fbc9b1aad794cef2bbd -->
**`jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts`**

- 源码声明的类型、组件或调用边界：`MAX_RECORDING_DURATION_MS`, `MIME_TYPE_CANDIDATES`, `TaskAsrOptions`, `TaskAsrResponse`, `preferredMimeType`, `blobBase64`, `reader`, `result`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useRef, useState } from 'react';`；`import { webRequest } from '../../services/webClient';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/taskAsr/useTaskAsr.ts#L1-L186)。
<!-- /kb:file -->
