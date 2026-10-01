---
title: "components-ui 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-ui 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/Button/Button.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0a69f1de0c65cbb3b10609e1e3b777710bc0537f2bb7ceae8ba51ebac214fdd2 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/Button/Button.tsx`**

- 源码声明的类型、组件或调用边界：`ButtonHTMLAttributes`, `ButtonBaseProps`, `TextButtonProps`, `IconButtonProps`, `ButtonProps`, `Button`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';`；`import { Loading } from '../Loading/Loading';`；`import './Button.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/Button/Button.tsx#L1-L50)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/CategoryTabs/CategoryTabs.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=50be0e1bfe2756840adb7973d3e339102b7c23791a54dfc39fc883d5a6da6b3b -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/CategoryTabs/CategoryTabs.tsx`**

- 源码声明的类型、组件或调用边界：`CategoryTabsOption`, `CategoryTabsProps`, `CategoryTabs`, `scrollByPage`, `el`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`；`import { useLayoutEffect } from 'react';`；`import { ChevronLeft, ChevronRight } from 'lucide-react';`；`import { useHorizontalScrollEdges } from '../../../hooks';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/CategoryTabs/CategoryTabs.tsx#L1-L81)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/CloseButton/CloseButton.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8f1b3a1a1e9c16027d3c1d13274800f9498df44a6bba4c58525a2feb38ccf8c6 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/CloseButton/CloseButton.tsx`**

- 源码声明的类型、组件或调用边界：`CloseButton`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/CloseButton/CloseButton.tsx#L1-L25)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/CollapsibleText/CollapsibleText.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4464d1d3860194ed82ae024d9011a87b391485596164bafd2c8121555fea6987 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/CollapsibleText/CollapsibleText.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `CollapsibleTextProps`, `CollapsibleText`, `contentRef`, `content`, `updateOverflow`, `lineHeight`, `nextOverflowing`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useLayoutEffect, useRef, useState, type ReactNode } from 'react';`；`import './CollapsibleText.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/CollapsibleText/CollapsibleText.tsx#L1-L55)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/DetailPromptChip/DetailPromptChip.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4ba201fbd0b025158641e8453234ff50d76d9b09d15775d1e8f22f2d72780013 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/DetailPromptChip/DetailPromptChip.tsx`**

- 源码声明的类型、组件或调用边界：`DetailPromptChipProps`, `DetailPromptChip`, `classes`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/DetailPromptChip/DetailPromptChip.tsx#L1-L45)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/DetailSection/DetailSection.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b01e5601662250505dda4a7a8cc08de875646d6c078110f3af4ced1aa0ee065e -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/DetailSection/DetailSection.tsx`**

- 源码声明的类型、组件或调用边界：`DetailSectionProps`, `DetailSection`, `classes`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`；`import './DetailSection.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/DetailSection/DetailSection.tsx#L1-L22)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/Dialog/Dialog.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ecdfd7053215ab32bb035a8a020396ac028860316a7838a23765e03226b4cbbe -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/Dialog/Dialog.tsx`**

- 源码声明的类型、组件或调用边界：`ReactNode`, `Dialog`, `dialogRef`, `pressedOnBackdrop`, `dialog`, `onBackdrop`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useRef, type ReactNode } from 'react';`；`import './Dialog.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/Dialog/Dialog.tsx#L1-L50)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/DropdownMenu/DropdownMenu.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=da47b0dd544c874ea660237c0ea12f1e2b63c65054102761bdb16637258268e5 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/DropdownMenu/DropdownMenu.tsx`**

- 源码声明的类型、组件或调用边界：`ButtonHTMLAttributes`, `CSSProperties`, `HTMLAttributes`, `KeyboardEvent`, `MouseEvent`, `MutableRefObject`, `ReactElement`, `ReactNode`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import { createPortal } from 'react-dom';`；`import './DropdownMenu.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/DropdownMenu/DropdownMenu.tsx#L1-L385)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/DropdownMenu/index.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6da17b2bdd3706a0585a0b1c2d6cc5d5782e098caa24d95cf52c1c58cb6ae5c6 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/DropdownMenu/index.ts`**

- 源码声明的类型、组件或调用边界：`DropdownMenuSide`, `DropdownMenuAlign`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/DropdownMenu/index.ts#L1-L8)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/EntityAvatar/EntityAvatar.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d1be8924f219e48eb6805c40da1625177f20163a077f225f1dcc40a95046963e -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/EntityAvatar/EntityAvatar.tsx`**

- 源码声明的类型、组件或调用边界：`EntityAvatarProps`, `EntityAvatar`, `fallback`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useState } from 'react';`；`import { getSkillAvatar } from '../../../utils/skillAvatar';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/EntityAvatar/EntityAvatar.tsx#L1-L43)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/EntityHeader/EntityHeader.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a1e1fe22340e71a22f06691aba2fc53b7e057b15969e0a84de0e410bae95e2b9 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/EntityHeader/EntityHeader.tsx`**

- 源码声明的类型、组件或调用边界：`MouseEvent`, `EntityImageAvatar`, `EntityHeaderAvatar`, `EntityHeaderTagItem`, `EntityHeaderTag`, `normalizeTag`, `EntityTag`, `isEntityImageAvatar`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { type MouseEvent, type ReactNode, useLayoutEffect, useRef, useState } from 'react';`；`import { EntityAvatar } from '../EntityAvatar/EntityAvatar';`；`import { useAdaptiveTooltip } from '../../../hooks/useAdaptiveTooltip';`；`import './EntityHeader.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/EntityHeader/EntityHeader.tsx#L1-L205)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/FilePreviewContent.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1daa041214b9a6ff924c5c74fef56accd587e2c967ce1ea65d3fc370a85da930 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/FilePreviewContent.tsx`**

- 源码声明的类型、组件或调用边界：`FilePreviewStatus`, `FilePreviewContentFile`, `FilePreviewContentLabels`, `FilePreviewContentProps`, `FilePreviewContent`, `isMarkdown`, `isPython`, `isJson`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useMemo, useState } from 'react';`；`import { ArrowDownToLine } from 'lucide-react';`；`import { MarkdownRenderer } from '../../MarkdownRenderer';`；`import { CodePreview } from '../../ArtifactsPanel/CodePreview';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/FilePreviewContent.tsx#L1-L217)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/FilePreviewIcon.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6bead54bb9d37940c4bb0b53a815240985fa1213a8c98e8fdeb1fb6594c29ba3 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/FilePreviewIcon.tsx`**

- 源码声明的类型、组件或调用边界：`FilePreviewIconType`, `SvgComponent`, `FILE_PREVIEW_ICON_COMPONENTS`, `FilePreviewIconProps`, `FilePreviewIcon`, `iconType`, `Icon`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ComponentType, SVGProps } from 'react';`；`import archiveIcon from '../../../assets/file-preview/archive.svg?react';`；`import audioIcon from '../../../assets/file-preview/audio.svg?react';`；`import codeIcon from '../../../assets/file-preview/code.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/FilePreviewIcon.tsx#L1-L54)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/FilePreviewPanel.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=59b023f81a490a0627e1d57fe9f76832ad80c2a4deb18f003bdcf058c0249868 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/FilePreviewPanel.tsx`**

- 源码声明的类型、组件或调用边界：`FilePreviewPanelProps`, `FilePreviewPanel`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`；`import './FilePreviewPanel.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/FilePreviewPanel.tsx#L1-L22)。
<!-- /kb:file -->
