---
title: "components-desktoptexteditcontextmenu 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-desktoptexteditcontextmenu 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/DesktopTextEditContextMenu/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2bed10f3e51de1989c657ef65b5e71b41d3ff852a000ee5588b63224a7fc7d8c -->
**`jiuwenswarm/channels/web/frontend/src/components/DesktopTextEditContextMenu/index.tsx`**

- 源码声明的类型、组件或调用边界：`MouseEvent`, `TextEditAction`, `TextEditCapabilities`, `TextEditTarget`, `MenuState`, `MENU_WIDTH`, `MENU_HEIGHT`, `clampMenuPosition`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState, useCallback, type MouseEvent as ReactMouseEvent } from 'react';`；`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`；`import { isDesktopShell } from '../../features/workspace/localFilePicker';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/DesktopTextEditContextMenu/index.tsx#L1-L169)。
<!-- /kb:file -->
