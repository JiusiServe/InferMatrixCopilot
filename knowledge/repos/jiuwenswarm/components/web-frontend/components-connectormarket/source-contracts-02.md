---
title: "components-connectormarket 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-connectormarket 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/RegisterMcpPage.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a306c3253fe114d5ad1cb29644bca41c3806bc2c791a2ab9dc3b738e0a32f51c -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/RegisterMcpPage.tsx`**

- 源码声明的类型、组件或调用边界：`McpConfigType`, `KeyValueRow`, `rowSeq`, `newRow`, `rowsFromArray`, `rowsFromRecord`, `entries`, `ParsedMcpConfig`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Minus, Plus } from 'lucide-react';`；`import { useConnectorStore } from '../../stores/connectorStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/RegisterMcpPage.tsx#L1-L480)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/Toast.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f08f3414671a7d2f41ce02bc052f952951bb8ecd411f67db5089b57693670a26 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/Toast.tsx`**

- 源码声明的类型、组件或调用边界：`ToastProps`, `Toast`, `isError`, `timer`, `palette`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect } from 'react';`；`import { AlertCircle, CheckCircle2, X } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/Toast.tsx#L1-L55)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/TruncatedText.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5bf24d0158d0ec792fd2744c0764911c9282a5d40cf9747713e15f7ea7ffefc2 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/TruncatedText.tsx`**

- 源码声明的类型、组件或调用边界：`TruncatedTextProps`, `TruncatedText`, `ref`, `el`, `check`, `observer`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useLayoutEffect, useRef, useState } from 'react';`；`import { useAdaptiveTooltip } from '../../hooks/useAdaptiveTooltip';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/TruncatedText.tsx#L1-L37)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/UploadFileCreateModal.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=28f67f2694a20dc45ec7f28ef8d50f052621bedb9357a0815f136446f42703df -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/UploadFileCreateModal.tsx`**

- 源码声明的类型、组件或调用边界：`LocalFilePick`, `UploadFileCreateModalProps`, `ACCEPTED_EXTENSIONS`, `DROP_ZONE_CLASS`, `DROP_ACCEPT_WINDOW_MS`, `isAcceptedFilename`, `lower`, `formatFileSize`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useRef, useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`；`import { X, UploadCloud, Info, FileArchive, Loader2 } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/UploadFileCreateModal.tsx#L1-L243)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/icons.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d4b41bd6b6625d43942f9537757d69b7081b6b75096524ffd1cd108a7daf4477 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/icons.tsx`**

- 源码声明的类型、组件或调用边界：`ExtensionIcon`, `NewConversationIcon`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import ExtensionAsset from '../../assets/agent-management/extension.svg?react';`；`import NewConversationAsset from '../../assets/agent-management/new-conversation.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/icons.tsx#L1-L10)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1f9012e2b402f8df1e60e1d56180274a080b85320b8b11c7105ab072fefd6372 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx`**

- 源码声明的类型、组件或调用边界：`TopTab`, `pendingManageView`, `requestManageView`, `View`, `ConnectorMarketPanelProps`, `ConnectorMarketPanel`, `kind`, `loadConnectorList`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { useConnectorStore } from '../../stores/connectorStore';`；`import { usePluginPackageStore } from '../../stores/pluginPackageStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx#L1-L320)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/mcpState.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0dab6b5c84ce8a36c91b85e51273eca84cec15e57c67e4c92e1a093d0f75af88 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/mcpState.ts`**

- 源码声明的类型、组件或调用边界：`McpCardState`, `McpCardInput`, `deriveCardState`, `busyLabelKey`, `deriveMcpAvailability`, `nextMcpQuickAction`, `derivePluginCardState`, `cardStateToStatusFilter`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ConnectorSummary, McpBusyKind } from '../../types/connector';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/mcpState.ts#L1-L130)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/useClickOutside.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=473431d13495e2bb007954f8bd765c21a2c5880d92e2007ce012a34f3b3699fa -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/useClickOutside.ts`**

- 源码声明的类型、组件或调用边界：`useClickOutside`, `handler`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/useClickOutside.ts#L1-L13)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/usePendingConnectorFlow.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6465282bed3fc4f11f57db6ff74cd7285767cf34e99c8f903f82d8c1ef6f0cc2 -->
**`jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/usePendingConnectorFlow.tsx`**

- 源码声明的类型、组件或调用边界：`PendingConnectorAbortReason`, `PendingConnectorFlow`, `findStoredConnector`, `state`, `ensurePendingConnector`, `store`, `connector`, `assetId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import { useConnectorStore } from '../../stores/connectorStore';`；`import type { ConnectorConnectResponse, ConnectorSummary } from '../../types/connector';`；`import { ConnectTokenModal } from './ConnectTokenModal';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/usePendingConnectorFlow.tsx#L1-L198)。
<!-- /kb:file -->
