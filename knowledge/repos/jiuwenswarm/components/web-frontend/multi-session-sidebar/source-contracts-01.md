---
title: "multi-session-sidebar 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# multi-session-sidebar 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ConversationSidebar.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e6b489f80f749bbda0a737bee9c9382b21139eaa0546d52837b1d3c1ca286765 -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ConversationSidebar.tsx`**

- 源码声明的类型、组件或调用边界：`ChatRuntime`, `SidebarCronJob`, `UNREAD_KEY`, `RELATIVE_TIME_REFRESH_MS`, `NewConversationOptions`, `isDefaultProject`, `ConversationSidebarProps`, `ConversationListItemProps`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react';`；`import { createPortal } from 'react-dom';`；`import { Check, ChevronDown, CircleAlert, Code2, Workflow } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ConversationSidebar.tsx#L1-L1255)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ProjectArchiveDialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2637b4ff0ca9d9e04e65b569621a8e6749cc954a8300dd2ecd802b04ac15098a -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ProjectArchiveDialog.tsx`**

- 源码声明的类型、组件或调用边界：`ProjectArchiveDialogProps`, `ProjectArchiveDialog`, `titleId`, `title`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useId } from 'react';`；`import { X } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`；`import { Button, Dialog } from '../../components/ui';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ProjectArchiveDialog.tsx#L1-L73)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ProjectCreateMenu.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d89b2bbc19f2b8dfc89812029e6edd362f14eba449149b8ce1fb42c95adb117a -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ProjectCreateMenu.tsx`**

- 源码声明的类型、组件或调用边界：`ProjectCreateMode`, `ProjectCreateMenuProps`, `ProjectCreateMenu`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/ProjectCreateMenu.tsx#L1-L44)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/SidebarActionMenu.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=704a1693295c1694d564905c145f3bc4f2ab87582fb18e402c73f98fe4a93305 -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/SidebarActionMenu.tsx`**

- 源码声明的类型、组件或调用边界：`SidebarActionMenuProps`, `SidebarActionMenu`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../comp`；`import type { SidebarMenuItem, TooltipHandlers } from './SidebarMenu.types';`；`import MoreIcon from '../../assets/work-mode/more-rimless.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/SidebarActionMenu.tsx#L1-L69)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/SidebarMenu.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=262d6fb1265ecbe57bc415af7d0fa3d55a9755048d35ee179048a2d008e36c58 -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/SidebarMenu.tsx`**

- 源码声明的类型、组件或调用边界：`SidebarMenuSharedProps`, `SidebarMenuProps`, `SidebarMenu`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useTranslation } from 'react-i18next';`；`import type { ProjectInfo, Session } from '../../types';`；`import { SidebarActionMenu } from './SidebarActionMenu';`；`import type { TooltipHandlers } from './SidebarMenu.types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/SidebarMenu.tsx#L1-L60)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/SidebarMenu.types.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d6e177587d16fd691c91d2a590f8487cb5a7f95608d72b1d24083ac32bc8852a -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/SidebarMenu.types.ts`**

- 源码声明的类型、组件或调用边界：`SidebarMenuItem`, `TooltipHandlers`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/SidebarMenu.types.ts#L1-L18)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/projectArchiveModel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c4e340a3c94a20c2499d2ffda5f37f13c3614e03b4bb346d6ac4ac3b51309e7c -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/projectArchiveModel.ts`**

- 源码声明的类型、组件或调用边界：`resolveProjectArchiveSessionCount`, `nonPinnedCount`, `pinnedOrdinaryCount`, `belongsToProject`, `isCronSession`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ProjectInfo, Session } from '../../types';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/projectArchiveModel.ts#L1-L21)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/projectCreateErrors.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0ce8e7b468ee60783d3eff62dd222c51d53d4c40780b095ba52d7bb296f86d07 -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/projectCreateErrors.ts`**

- 源码声明的类型、组件或调用边界：`projectCreateErrorKey`, `message`, `code`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/projectCreateErrors.ts#L1-L16)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/sidebarMenuSchema.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dfcc5307f21ce4e0b2060eb773feb314309f1fa9d7b48c0e9160fc75bfd98927 -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/sidebarMenuSchema.ts`**

- 源码声明的类型、组件或调用边界：`Translate`, `SidebarMenuItemDef`, `PIN_LABEL_PAIRS`, `getProjectMenuItems`, `batchItems`, `getSessionMenuItems`, `scope`, `pinLabels`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/sidebarMenuSchema.ts#L1-L68)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/sidebarModel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bc9ef12b2f1d79a671be19aeb41143274e5c2d6a898c32146adad9cc0104bb57 -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/sidebarModel.ts`**

- 源码声明的类型、组件或调用边界：`SessionIndicator`, `Translate`, `RuntimeLike`, `SessionLike`, `normalizeActivityTime`, `parsed`, `getSessionActivityAt`, `getSessionIndicator`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/sidebarModel.ts#L1-L77)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/useSidebarMenu.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f1ad4aeaf7d779a8d65a62bf38a71c1b6e941362a50abc20fab4405b3ea3bb74 -->
**`jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/useSidebarMenu.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `SidebarMenuOptions`, `RenameTarget`, `Translate`, `isDefaultProject`, `isCronSession`, `getSessionTitle`, `raw`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createElement, useRef, useState, type ReactNode } from 'react';`；`import { flushSync } from 'react-dom';`；`import { Archive } from 'lucide-react';`；`import { useTranslation } from 'react-i18next';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/multi-session/sidebar/useSidebarMenu.tsx#L1-L642)。
<!-- /kb:file -->
