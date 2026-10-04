---
title: "components-logspanel 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-logspanel 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/LogsPanel/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4b6b28bb8ef56cc6bfee4b9251eae37c59db7d60b28d71e7f49d500c005db3c7 -->
**`jiuwenswarm/channels/web/frontend/src/components/LogsPanel/index.tsx`**

- 源码声明的类型、组件或调用边界：`LogsPanelProps`, `WS_RECONNECT_EVENT`, `formatLogEntries`, `parseJsonlTail`, `lines`, `isDebugLogEntry`, `record`, `LogsPanel`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useMemo, useRef, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/LogsPanel/index.tsx#L1-L221)。
<!-- /kb:file -->
