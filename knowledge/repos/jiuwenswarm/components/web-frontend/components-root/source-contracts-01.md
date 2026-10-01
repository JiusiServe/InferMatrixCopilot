---
title: "components-root 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-root 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ExternalCliAgentsSection.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=87da13264fdc50ee1dda87dae9995ee99042559f313177a5af5f8d4728263210 -->
**`jiuwenswarm/channels/web/frontend/src/components/ExternalCliAgentsSection.tsx`**

- 源码声明的类型、组件或调用边界：`ExternalCliAgentKind`, `ExternalCliDetectResult`, `ExternalCliDependencyInstallStatus`, `ExternalCliConfigSaveResult`, `ExternalCliPendingChoice`, `EXTERNAL_CLI_AGENT_KINDS`, `EXTERNAL_CLI_AUTO_DETECT_DELAY_MS`, `EXTERNAL_CLI_AGENT_CONFIG_KEYS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useRef, useState } from 'react';`；`import { AlertCircle, Check, CheckCircle2, Copy, FileSearch, Loader2, RefreshCw } from 'lucide-react`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ExternalCliAgentsSection.tsx#L1-L539)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ExternalCliInstallDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=771ded0c4529fc0c4931be63c348eb6ae68a10679cb41fbad65b4fcd0509af04 -->
**`jiuwenswarm/channels/web/frontend/src/components/ExternalCliInstallDialog.tsx`**

- 源码声明的类型、组件或调用边界：`InstallStatuses`, `formatBytes`, `units`, `amount`, `unitIndex`, `digits`, `formatEta`, `rounded`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect } from 'react';`；`import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import type { ExternalCliAgentKind, ExternalCliDependencyInstallStatus } from './ExternalCliAgentsSe`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ExternalCliInstallDialog.tsx#L1-L192)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/TeamTaskEvents.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c98a1570bdc5cd02f679eeb1f197b08d46cdbf355bad57c5b3bba880914db258 -->
**`jiuwenswarm/channels/web/frontend/src/components/TeamTaskEvents.tsx`**

- 源码声明的类型、组件或调用边界：`TeamTaskEvent`, `TeamTaskEventsProps`, `TeamTaskEvents`, `formatTime`, `date`, `getEventName`, `match`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/TeamTaskEvents.tsx#L1-L55)。
<!-- /kb:file -->
