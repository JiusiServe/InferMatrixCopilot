---
title: "components-markdownrenderer 源码接口与集成边界 02"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# components-markdownrenderer 源码接口与集成边界 02

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/markdownPlugins.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7bb92cc2eba00dc5b5c448ac638f39b6d1a6298d58db624de2f43ac7154b41f8 -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/markdownPlugins.ts`**

- 源码声明的类型、组件或调用边界：`KATEX_OPTIONS`, `KATEX_HTML_ONLY_OPTIONS`, `MARKDOWN_REMARK_PLUGINS`, `MARKDOWN_REHYPE_PLUGINS`, `MARKDOWN_REHYPE_HTML_ONLY_PLUGINS`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { PluggableList } from 'unified';`；`import rehypeKatex from 'rehype-katex';`；`import type { Options as RehypeKatexOptions } from 'rehype-katex';`；`import rehypeSlug from 'rehype-slug';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/markdownPlugins.ts#L1-L14)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/markdownTransforms.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2712f05782ab522c4f249d16f5922a2fcbddab9f3edf7c81a1d316187a0515c9 -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/markdownTransforms.ts`**

- 源码声明的类型、组件或调用边界：`OpenFence`, `getOpeningFence`, `match`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/markdownTransforms.ts#L1-L89)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/math/remarkLatexDelimiters.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=81d0e5183bb4e2f2025e0400b93ac1d952cbd546a0eb121d4b905325a845c686 -->
**`jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/math/remarkLatexDelimiters.ts`**

- 源码声明的类型、组件或调用边界：`TokenTypeMap`, `LatexDelimiterTokens`, `MarkdownProcessorData`, `BACKSLASH`, `LEFT_PARENTHESIS`, `RIGHT_PARENTHESIS`, `LEFT_SQUARE_BRACKET`, `RIGHT_SQUARE_BRACKET`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import type { Extension as FromMarkdownExtension, Handle } from 'mdast-util-from-markdown';`；`import type { Code, Construct, Effects, Extension as MicromarkExtension, State, Token } from 'microm`；`import type { Processor } from 'unified';`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/MarkdownRenderer/math/remarkLatexDelimiters.ts#L1-L193)。
<!-- /kb:file -->
