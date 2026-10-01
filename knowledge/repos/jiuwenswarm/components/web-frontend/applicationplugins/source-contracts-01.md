---
title: "applicationplugins 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# applicationplugins 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/applicationPlugins/ApplicationPluginOutlet.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8347313ce0204e648a70485829b70eaf238545d28f5099eca37a3758747041cd -->
**`jiuwenswarm/channels/web/frontend/src/applicationPlugins/ApplicationPluginOutlet.tsx`**

- 源码声明的类型、组件或调用边界：`BundledPluginModule`, `bundledModules`, `bundledComponents`, `bundledSettingsComponents`, `bundledTaskInputActions`, `bundledTaskRuntimes`, `module`, `applicationPluginSettingsComponent`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ComponentType } from 'react';`；`import type {`；`import './applicationPlugins.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/applicationPlugins/ApplicationPluginOutlet.tsx#L1-L82)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/applicationPlugins/ApplicationTaskControls.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b657e3c9eb8365dd2d456e65aaa31ae59c53fc0d245d0570e1835017ef1ac0d9 -->
**`jiuwenswarm/channels/web/frontend/src/applicationPlugins/ApplicationTaskControls.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `ApplicationTaskAction`, `DRAG_TYPE`, `ApplicationTaskControls`, `sessions`, `tasks`, `task`, `pending`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState, type ReactNode } from 'react';`；`import { ArrowUpToLine, GripVertical, MoreHorizontal, X } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import { controlApplicationTask, useApplicationTaskStore, type ApplicationTaskAction } from './taskP`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/applicationPlugins/ApplicationTaskControls.tsx#L1-L157)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/applicationPlugins/manifest.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=622cf59ba59099cea640be790eee7448ba55ba498ffeae0572e08930be75c96c -->
**`jiuwenswarm/channels/web/frontend/src/applicationPlugins/manifest.ts`**

- 源码声明的类型、组件或调用边界：`isContribution`, `item`, `normalizeApplicationPluginManifest`, `manifest`, `enabledApplicationPlugins`, `fetchApplicationPlugins`, `response`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ApplicationPluginContribution, ApplicationPluginManifest } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/applicationPlugins/manifest.ts#L1-L36)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/applicationPlugins/taskProgressStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=db3c2f22d2fee2caab07e7877b5760a6424c13b463f966e7381524e6d5e7cccb -->
**`jiuwenswarm/channels/web/frontend/src/applicationPlugins/taskProgressStore.ts`**

- 源码声明的类型、组件或调用边界：`ApplicationTaskStatus`, `ApplicationTaskAction`, `TaskController`, `controllers`, `registerApplicationTaskController`, `controlApplicationTask`, `controller`, `ApplicationTaskProgress`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { create } from 'zustand';`；`import type { TeamTask } from '../stores/sessionStore';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/applicationPlugins/taskProgressStore.ts#L1-L111)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/applicationPlugins/types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=df33976d119202af31faab36cc78bd1125a037a0fbeaf01f82d8b94a336963e1 -->
**`jiuwenswarm/channels/web/frontend/src/applicationPlugins/types.ts`**

- 源码声明的类型、组件或调用边界：`ApplicationPluginNavKey`, `ApplicationPluginContribution`, `ApplicationPluginManifest`, `ApplicationPluginSettingsProps`, `ApplicationPluginTaskInputActionProps`, `ApplicationPluginTaskRuntimeProps`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`；`import type { FileDownloadItem, ToolCall, ToolResult } from '../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/applicationPlugins/types.ts#L1-L58)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/applicationPlugins/useApplicationPlugins.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6b3bf1fd7d360e976b13bca098a13d34ac2cf7b69b6bdfd22f955f0d0b123122 -->
**`jiuwenswarm/channels/web/frontend/src/applicationPlugins/useApplicationPlugins.ts`**

- 源码声明的类型、组件或调用边界：`ApplicationPluginsState`, `useApplicationPlugins`, `refresh`, `controller`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useState } from 'react';`；`import { fetchApplicationPlugins } from './manifest';`；`import type { ApplicationPluginContribution } from './types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/applicationPlugins/useApplicationPlugins.ts#L1-L59)。
<!-- /kb:file -->
