---
title: "components-fileicon 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-fileicon 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/FileIcon/fileIconModel.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4cfb47297efa1b2ee980c5013c2ccd8cb2b8f6d62c5f56b24f6c5780e4630bad -->
**`jiuwenswarm/channels/web/frontend/src/components/FileIcon/fileIconModel.ts`**

- 源码声明的类型、组件或调用边界：`FileIconType`, `EXTENSION_GROUPS`, `COMPOUND_EXTENSION_TO_TYPE`, `EXTENSION_TO_TYPE`, `basename`, `parts`, `getFileExtensionLabel`, `name`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/FileIcon/fileIconModel.ts#L1-L84)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/FileIcon/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d8bb82c04d7304eec04b7412f3c9bdeaf3a2470c75849c3d6840292e2f1e951d -->
**`jiuwenswarm/channels/web/frontend/src/components/FileIcon/index.tsx`**

- 源码声明的类型、组件或调用边界：`FileIconType`, `FILE_ICON_ASSETS`, `FileIconBaseProps`, `FileIconSourceProps`, `FileIconProps`, `resolveIconType`, `FileIcon`, `iconType`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { CSSProperties } from 'react';`；`import archiveIcon from '../../assets/file-icons/archive.svg';`；`import audioIcon from '../../assets/file-icons/audio.svg';`；`import codeIcon from '../../assets/file-icons/code.svg';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/FileIcon/index.tsx#L1-L64)。
<!-- /kb:file -->
