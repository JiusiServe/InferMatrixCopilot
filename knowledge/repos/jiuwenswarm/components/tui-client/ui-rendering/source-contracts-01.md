---
title: "ui-rendering 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# ui-rendering 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/tui/frontend/src/ui/rendering/text.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=406a0eb57e9cc313e5f2cc3a85ea31d9449fa3765bb181574041697d2e8c57cd -->
**`jiuwenswarm/channels/tui/frontend/src/ui/rendering/text.ts`**

- 源码声明的类型、组件或调用边界：`DefaultTextStyle`, `emptyLine`, `padToWidth`, `clipped`, `padding`, `summarize`, `raw`, `prefixedLines`；这是词法声明索引，不把局部变量当成对外导出 API。
- 集成边界的导入/加载声明：`import {`；`import { markdownTheme } from "../theme.js";`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/tui/frontend/src/ui/rendering/text.ts#L1-L109)。
<!-- /kb:file -->
