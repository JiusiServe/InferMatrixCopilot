---
title: "components-ui 源码接口与集成边界 03"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-ui 源码接口与集成边界 03

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/Switch/Switch.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2b1f1e682cb753a6f036db62c22c8e390cc4027ee27b071c7dfe6e13751dfcee -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/Switch/Switch.tsx`**

- 源码声明的类型、组件或调用边界：`ButtonHTMLAttributes`, `SwitchProps`, `Switch`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { forwardRef, type ButtonHTMLAttributes } from 'react';`；`import './Switch.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/Switch/Switch.tsx#L1-L26)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/Tabs/Tabs.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c5b615260bf6e0f9efdb3a2e2e0e5e83dac7b92c8c60b7c9ab0adfb5c5b9b266 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/Tabs/Tabs.tsx`**

- 源码声明的类型、组件或调用边界：`TabsItem`, `TabsProps`, `Tabs`, `classes`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { AriaRole, ReactNode } from 'react';`；`import './Tabs.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/Tabs/Tabs.tsx#L1-L59)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/Tag/Tag.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5427d21dfb10bab7d6733dd78635c9d62a5ef9893aa07293445c24378ccafa4b -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/Tag/Tag.tsx`**

- 源码声明的类型、组件或调用边界：`HTMLAttributes`, `TagVariant`, `TagProps`, `Tag`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { type HTMLAttributes, type ReactNode } from 'react';`；`import './Tag.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/Tag/Tag.tsx#L1-L17)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/Textarea/Textarea.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=10c760b34057ab7748fe7f6dd99646c9374d9d65d7366dbf8386f43b3fd5ce6b -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/Textarea/Textarea.tsx`**

- 源码声明的类型、组件或调用边界：`TextareaHTMLAttributes`, `TextareaProps`, `Textarea`, `innerRef`, `resizeTextArea`, `el`, `handleChange`, `el`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { forwardRef, useCallback, useEffect, useRef, useImperativeHandle, type TextareaHTMLAttribute`；`import './Textarea.css';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/Textarea/Textarea.tsx#L1-L97)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/Toast/Toast.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c6eb470f2109e5be93de3152dd2dbac9151b093f40c06a72a281a2fa0057429c -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/Toast/Toast.tsx`**

- 源码声明的类型、组件或调用边界：`ToastRecord`, `VARIANT_ICON`, `ToastItem`, `timerId`, `StatusIcon`, `hasActions`, `ToastStack`, `records`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useEffect, useSyncExternalStore } from 'react';`；`import { createPortal } from 'react-dom';`；`import { AlertTriangle, CircleAlert, CircleCheck, X } from 'lucide-react';`；`import type { LucideIcon } from 'lucide-react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/Toast/Toast.tsx#L1-L82)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/Toast/toastStore.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=aa80ec8d2f7a755eafa2afa0201c9ba386a283c331a892eb594f1752d273e854 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/Toast/toastStore.ts`**

- 源码声明的类型、组件或调用边界：`ToastAction`, `ToastVariant`, `ToastConfig`, `ToastRecord`, `DEFAULT_DURATION_SECONDS`, `TOAST_EXIT_ANIMATION_MS`, `records`, `nextKey`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { ReactNode } from 'react';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/Toast/toastStore.ts#L1-L127)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/ui/index.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5aeb8bd435035f78b5633c53414e185f4eaa46a0bd160889c32ef8e971c6e9f3 -->
**`jiuwenswarm/channels/web/frontend/src/components/ui/index.ts`**

- 源码声明的类型、组件或调用边界：`ButtonProps`, `CollapsibleTextProps`, `InfoCardProps`, `InputProps`, `TextareaProps`, `SelectOption`, `SwitchProps`, `RadioOption`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ui/index.ts#L1-L72)。
<!-- /kb:file -->
