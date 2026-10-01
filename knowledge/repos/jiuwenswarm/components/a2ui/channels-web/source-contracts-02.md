---
title: "channels-web 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# channels-web 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/formDefaults.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=465b6abe25a26b936a5f7d619168e8c475787bd21cc0bf048bb89a1fbd9c92de -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/formDefaults.ts`**

- 源码声明的类型、组件或调用边界：`UnknownRecord`, `isDevA2UIDiagnosticEnabled`, `a2uiDebug`, `a2uiWarn`, `a2uiError`, `isRecord`, `normalizeA2UIPath`, `trimmed`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { DataValue } from '@a2ui/react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/formDefaults.ts#L1-L219)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/a2ui/rendererRegistry.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4fb65a951b26298cb6e8ad1e4e8366a43910877a5a40bda5c349e14d6ae7ce11 -->
**`jiuwenswarm/channels/web/frontend/src/features/a2ui/rendererRegistry.tsx`**

- 源码声明的类型、组件或调用边界：`A2UIProtocolVersion`, `A2UIRendererProps`, `a2uiV08Registry`, `applyOverrides`, `_overridesApplied`, `A2UIV08Renderer`, `current`, `rendererByVersion`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ComponentType } from 'react';`；`import { A2UIRenderer, ComponentRegistry } from '@a2ui/react';`；`import { A2UI_PROTOCOL_VERSION, type A2UIProtocolVersion } from './a2uiContent';`；`import { CheckBoxWithDefaults } from './CheckBoxWithDefaults';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/a2ui/rendererRegistry.tsx#L1-L72)。
<!-- /kb:file -->
