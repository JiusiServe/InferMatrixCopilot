---
title: "components-toolpanel 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-toolpanel 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ToolPanel/CollapsibleSection.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=020fac52bc1ef18a94b4e5a4ad9f5a7207ee4127e8e913c3546a4786d73e9823 -->
**`jiuwenswarm/channels/web/frontend/src/components/ToolPanel/CollapsibleSection.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `CollapsibleSectionProps`, `CollapsibleSection`, `expanded`, `handleToggleCollapse`, `nextCollapsed`, `handleExpandAll`, `overflowCount`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState, type ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import { Maximize2 } from 'lucide-react';`；`import collapseIcon from '../../assets/work-mode/collapse.svg';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ToolPanel/CollapsibleSection.tsx#L1-L149)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ToolPanel/ReadOnlyFileModal.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6c07a7e4949c1bbf28607ad1c2a8e53b392a3f74f20eae210fa04852b998183e -->
**`jiuwenswarm/channels/web/frontend/src/components/ToolPanel/ReadOnlyFileModal.tsx`**

- 源码声明的类型、组件或调用边界：`ReadOnlyFileModalProps`, `isPreviewableFile`, `lowerName`, `isMarkdownFile`, `lowerName`, `isJsonFile`, `ReadOnlyFileModal`, `handleKeyDown`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { useTranslation } from 'react-i18next';`；`import ReactMarkdown from 'react-markdown';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ToolPanel/ReadOnlyFileModal.tsx#L1-L218)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ToolPanel/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=41c6a5137a0ee4a91b34dfbe5bac26fd5ebe3a7eea4caacce5b918d5088dc3f2 -->
**`jiuwenswarm/channels/web/frontend/src/components/ToolPanel/index.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `TabType`, `SingleAgentToolTab`, `todoItemToTeamTask`, `statusMap`, `ts`, `ToolPanelProps`, `isEmptyValue`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import { useChatStore, useSessionStore, useTodoStore } from '../../stores';`；`import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';`；`import { Info } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ToolPanel/index.tsx#L1-L789)。
<!-- /kb:file -->
