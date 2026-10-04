---
title: "components-ui 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-ui 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/FilePreviewTree.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4bc7d48ed5904bf3f43178721e7d5e6489e29f1f5e182ffc8bc851520e6ae450 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/FilePreviewTree.tsx`**

- 源码声明的类型、组件或调用边界：`FilePreviewStatus`, `FilePreviewTreeNode`, `FilePreviewTreeLabels`, `FilePreviewTreeProps`, `findExpandedDirectories`, `expanded`, `visit`, `item`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useState } from 'react';`；`import { ChevronDown, ChevronRight } from 'lucide-react';`；`import FolderAssetIcon from '../../../assets/work-mode/folder.svg?react';`；`import FolderFoldAssetIcon from '../../../assets/work-mode/folder-fold.svg?react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/FilePreviewTree.tsx#L1-L250)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/filePreviewShared.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7fca68e1ac762cff8cf89c994ad8c77f34f3a035cc646444b9e2b613bfe1c54c -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/filePreviewShared.ts`**

- 源码声明的类型、组件或调用边界：`DesktopSaveApiResult`, `FilePreviewStatus`, `FilePreviewIconType`, `CODE_FILE_PATTERN`, `IMAGE_FILE_PATTERN`, `MARKDOWN_FILE_PATTERN`, `getPreviewFileLabel`, `isCodeFileName`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { executeDesktopSave, type DesktopSaveApiResult } from '../../../utils/desktopSave';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/FilePreviewPanel/filePreviewShared.ts#L1-L263)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/FormDrawer/FormDrawer.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=887f419163fb8cb508cb2616ee2754010aee0b661460c612683df2b7ec3a309c -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/FormDrawer/FormDrawer.tsx`**

- 源码声明的类型、组件或调用边界：`FormDrawerProps`, `FormDrawer`, `drawerStyle`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode, Ref } from 'react';`；`import { createPortal } from 'react-dom';`；`import { useTranslation } from 'react-i18next';`；`import { Loader2 } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/FormDrawer/FormDrawer.tsx#L1-L98)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/HelpTips/HelpTips.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=26859689e957c9cec56c4ac3b1da385e80ec6a63331becbcd95f8bfb6cf0cadf -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/HelpTips/HelpTips.tsx`**

- 源码声明的类型、组件或调用边界：`HelpTips`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import './HelpTips.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/HelpTips/HelpTips.tsx#L1-L8)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/InfoCard/InfoCard.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=159bb4be66af792ec19f9d0e161e739ad5b54adecd58e157bdc2c553488a79b6 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/InfoCard/InfoCard.tsx`**

- 源码声明的类型、组件或调用边界：`InfoCardProps`, `InfoCard`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Plus } from 'lucide-react';`；`import type { HTMLAttributes, ReactNode } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/InfoCard/InfoCard.tsx#L1-L60)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/Input/Input.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d63be656f6b88218e9404fa15dac3c79ac237be8ae4a54e4b59518b2a5401154 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/Input/Input.tsx`**

- 源码声明的类型、组件或调用边界：`ChangeEvent`, `FocusEvent`, `InputHTMLAttributes`, `MouseEvent`, `ReactNode`, `Ref`, `PasswordVisibilityLabels`, `AllowClearConfig`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import { Eye, EyeOff, X } from 'lucide-react';`；`import './Input.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/Input/Input.tsx#L1-L249)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/Loading/Loading.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3a11cf20edf3de97a87a473c458d7971803a7f4578c2bf3c555a45a951fb76a9 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/Loading/Loading.tsx`**

- 源码声明的类型、组件或调用边界：`Loading`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Loader2 } from 'lucide-react';`；`import './Loading.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/Loading/Loading.tsx#L1-L18)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/LoadingSpinner/LoadingSpinner.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e7fd92bb3c3723ad998043541ca6eb4f4ec7181ac19d473f58f6e93609854c38 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/LoadingSpinner/LoadingSpinner.tsx`**

- 源码声明的类型、组件或调用边界：`LoadingSpinnerProps`, `LoadingSpinner`, `uid`, `maskId`, `clipId`, `gradientId`, `filterId`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useId } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/LoadingSpinner/LoadingSpinner.tsx#L1-L62)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/MarkdownPane/MarkdownPane.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fdcfbc99d737c8e8f377ac50059aa50b53fd37f6bb0f782aa25ef0c60ed11a39 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/MarkdownPane/MarkdownPane.tsx`**

- 源码声明的类型、组件或调用边界：`MarkdownPaneProps`, `MarkdownPane`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`；`import { MarkdownRenderer } from '../../MarkdownRenderer';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/MarkdownPane/MarkdownPane.tsx#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/PageCard/PageCard.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5448cf7e68ea08312b26d519b0248456f55c55f8089ec43c6eda74dad23e62a9 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/PageCard/PageCard.tsx`**

- 源码声明的类型、组件或调用边界：`KeyboardEvent`, `EntityHeaderAvatar`, `PageCardActionProps`, `PageCardAvatar`, `PageCardProps`, `PageCard`, `classNames`, `hasLabel`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { type KeyboardEvent, type MouseEvent, type ReactNode } from 'react';`；`import { EntityHeader, type EntityHeaderAvatar } from '../EntityHeader/EntityHeader';`；`import { useAdaptiveTooltip } from '../../../hooks/useAdaptiveTooltip';`；`import './PageCard.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/PageCard/PageCard.tsx#L1-L133)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/PageHeader/PageHeader.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5ff376b18c1e77dfe055250d836e306f92a0c4d0c5cad652578a1ce32040c37a -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/PageHeader/PageHeader.tsx`**

- 源码声明的类型、组件或调用边界：`PageHeaderProps`, `PageHeader`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/PageHeader/PageHeader.tsx#L1-L23)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/PageToolbar/PageToolbar.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=775adb882c8890bb650b9f50d9e0c2d64aa04c446b75693c14b52e9e3c6c1e36 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/PageToolbar/PageToolbar.tsx`**

- 源码声明的类型、组件或调用边界：`PageToolbarProps`, `PageToolbar`, `classes`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AriaRole, CSSProperties, ReactNode } from 'react';`；`import './PageToolbar.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/PageToolbar/PageToolbar.tsx#L1-L20)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/PageToolbarSearch/PageToolbarSearch.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7dba0b28cda6b6bc08509d5aaac9a052d399012d41cb85c8f75490de4afe8e98 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/PageToolbarSearch/PageToolbarSearch.tsx`**

- 源码声明的类型、组件或调用边界：`InputHTMLAttributes`, `PageToolbarSearchProps`, `WIDTH_STEPS`, `resolveWrapperWidth`, `PageToolbarSearch`, `wrapperRef`, `container`, `observer`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useRef, useState, type InputHTMLAttributes } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/PageToolbarSearch/PageToolbarSearch.tsx#L1-L78)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/RadioGroup/RadioGroup.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a73c221c00d29e855a887d7b008cd517228768a41c06d082fcf5617548f4116b -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/RadioGroup/RadioGroup.tsx`**

- 源码声明的类型、组件或调用边界：`RadioOption`, `RadioGroup`, `name`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useId } from 'react';`；`import './RadioGroup.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/RadioGroup/RadioGroup.tsx#L1-L46)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/Select/Select.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=afdab0df662a68a8838b6207d1dbdb241135d320c80a30ef02510d304158c116 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/Select/Select.tsx`**

- 源码声明的类型、组件或调用边界：`ButtonHTMLAttributes`, `CSSProperties`, `KeyboardEvent`, `ReactNode`, `SelectOption`, `SelectProps`, `TRIGGER_GAP`, `VIEWPORT_MARGIN`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import { createPortal } from 'react-dom';`；`import './Select.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/Select/Select.tsx#L1-L271)。
<!-- /kb:file -->
