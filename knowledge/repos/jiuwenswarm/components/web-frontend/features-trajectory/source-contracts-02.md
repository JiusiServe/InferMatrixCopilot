---
title: "features-trajectory 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# features-trajectory 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/icons/index.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0729311c3255e9dafc0bfba08c2a53190588556b605722d88f5bff5693aa2d6e -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/icons/index.tsx`**

- 源码声明的类型、组件或调用边界：`IconNewChatOutline16`, `IconSearchOutline16`, `IconGlobeOutline14`, `IconSettingsOutline14`, `IconSettingsOutline16`, `IconPanelLeftOutline16`, `IconEllipsisOutline16`, `IconPlusOutline16`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { IconProps } from './props.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/icons/index.tsx#L1-L874)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/icons/props.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=75bef92fb0f9e9e81158fb2e633b6565573010539b51d7c79610567b19a64086 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/icons/props.ts`**

- 源码声明的类型、组件或调用边界：`IconProps`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/icons/props.ts#L1-L10)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/CodeBlock.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f16b407a7191c36fa34b99c3e5dfa1a4d8bab62481a6d403c923302c5f033ac2 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/CodeBlock.tsx`**

- 源码声明的类型、组件或调用边界：`CodeBlockProps`, `CodeBlock`, `trimmed`, `loaded`, `html`, `rootRef`, `onCopy`, `text`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useMemo, useRef, useState, useSyncExternalStore } from 'react'`；`import clsx from 'clsx'`；`import { writeClipboard } from '../clipboard.ts'`；`import { grammarLoadCount, highlightToHtml, subscribeGrammarLoaded } from './highlight.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/CodeBlock.tsx#L1-L76)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/MarkdownText.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f38efb06055ab81418d06ef97b4c47314bde97544a64b7d7cf4794c2efb517a5 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/MarkdownText.tsx`**

- 源码声明的类型、组件或调用边界：`renderSettled`, `root`, `targets`, `context`, `blocks`, `section`, `StreamingRenderer`, `newlyFrozen`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { memo, useMemo, useRef } from 'react'`；`import type { ReactNode } from 'react'`；`import { IncrementalMarkdownParser } from './incremental.ts'`；`import { parseGfm, parseGfmWithMath } from './parse.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/MarkdownText.tsx#L1-L178)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/cjkFriendlyStrong.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=40de448944efeb3af098fb9ca8df9d5e1ed9b555d363d6fcc09956b65947740c -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/cjkFriendlyStrong.ts`**

- 源码声明的类型、组件或调用边界：`cjkCharacter`, `isCjkCharacter`, `tokenizeCjkFriendlyAttention`, `configuredAttentionMarkers`, `attentionMarkers`, `previous`, `before`, `marker`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { attention } from 'micromark-core-commonmark'`；`import { unicodePunctuation } from 'micromark-util-character'`；`import { classifyCharacter } from 'micromark-util-classify-character'`；`import { codes, constants } from 'micromark-util-symbol'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/cjkFriendlyStrong.ts#L1-L85)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/highlight.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=49c3e3d02d9051449e051fbd9096c1cae8cfd79294e392124dbb01ffe200d899 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/highlight.ts`**

- 源码声明的类型、组件或调用边界：`LangModule`, `LANGS`, `LAZY_GRAMMARS`, `LANG_ALIASES`, `cssVariablesTheme`, `regexEngine`, `singleton`, `BOOT_GRAMMAR_WARMUPS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createHighlighterCoreSync, createCssVariablesTheme } from 'shiki/core'`；`import { createJavaScriptRegexEngine, defaultJavaScriptRegexConstructor } from 'shiki/engine/javascr`；`import langTs from '@shikijs/langs/typescript'`；`import langBash from '@shikijs/langs/shellscript'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/highlight.ts#L1-L313)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/incremental.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c91f5ad7e7994f0aa55b1dee08b1af92528816db6f00a876dd9ff3cb00632b98 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/incremental.ts`**

- 源码声明的类型、组件或调用边界：`UNSTABLE_TAIL_BLOCKS`, `PositionedBlock`, `IncrementalBlocks`, `blockKey`, `offset`, `IncrementalMarkdownParser`, `base`, `blocks`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { Root, RootContent } from 'mdast'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/incremental.ts#L1-L132)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/katex.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a51ff66bf35f3df849844c61d5fca742eb68b2b53a9394b294ae14196dc374e1 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/katex.tsx`**

- 源码声明的类型、组件或调用边界：`styleObject`, `style`, `declaration`, `colon`, `name`, `key`, `domToReact`, `element`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { createElement } from 'react'`；`import type { CSSProperties, ReactNode } from 'react'`；`import katex from 'katex'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/katex.tsx#L1-L92)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/mathCompatibility.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4f853047ff86bc240443e69b23ec6dbdbaf19faf89cd439e267e3ce4892aee36 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/mathCompatibility.ts`**

- 源码声明的类型、组件或调用边界：`previousBackslash`, `tail`, `tokenizeBackslashMathText`, `start`, `open`, `between`, `afterCloseAttempt`, `dataStart`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { factorySpace } from 'micromark-factory-space'`；`import type {} from 'micromark-extension-math'`；`import { markdownLineEnding } from 'micromark-util-character'`；`import { codes, constants, types } from 'micromark-util-symbol'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/mathCompatibility.ts#L1-L351)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/parse.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5122707b94ee46779bf3e135513a7dd2c7ad658e86f72d0dfc46927e5cc28369 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/parse.ts`**

- 源码声明的类型、组件或调用边界：`parseGfm`, `parseGfmWithMath`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { Root } from 'mdast'`；`import { fromMarkdown } from 'mdast-util-from-markdown'`；`import { gfmFromMarkdown } from 'mdast-util-gfm'`；`import { mathFromMarkdown } from 'mdast-util-math'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/parse.ts#L1-L46)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/plain-text.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=93f765c83e358255b5b0554d37745a49d7a90d6619bceaf9b7d1a293d5919fd3 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/plain-text.ts`**

- 源码声明的类型、组件或调用边界：`MarkdownPlainTextMode`, `MarkdownPlainTextOptions`, `MarkdownNode`, `inlineText`, `compactInline`, `blockText`, `findFirstParagraph`, `text`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { parseGfm } from './parse.ts'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/plain-text.ts#L1-L123)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/render.tsx pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a25589f3d0e4534cb44239b3fcf45a436c5711d80e537ee7c3b398b2d52e2b58 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/render.tsx`**

- 源码声明的类型、组件或调用边界：`MarkdownCodeLabels`, `sanitizeUrl`, `remoteImageUrl`, `protocol`, `ReferenceTargets`, `createReferenceTargets`, `collectReferenceTargets`, `node`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { Fragment, createElement } from 'react'`；`import type { Key, ReactNode } from 'react'`；`import type * as Md from 'mdast'`；`import type {} from 'mdast-util-math'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/markdown/render.tsx#L1-L585)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/pointer-grace.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=edd2dfce246f9bfc5b5615a3af8adaee192655f4fc723086d13fb8b7b7cc0fb1 -->
**`jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/pointer-grace.ts`**

- 源码声明的类型、组件或调用边界：`POINTER_GRACE_MS`, `PointerGrace`, `usePointerGrace`, `timerRef`, `closeRef`, `cancel`, `arm`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import { useCallback, useEffect, useRef } from 'react'`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/features/trajectory/primitives/pointer-grace.ts#L1-L55)。
<!-- /kb:file -->
