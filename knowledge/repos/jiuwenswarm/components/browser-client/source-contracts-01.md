---
title: "browser-client 源码接口与集成边界 01"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: []
---

# browser-client 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/vite.config.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c472d80b8a57a6c1321560f9698bc0d3b53dcbd6dfbda14e7ba3ce7747ea6b95 -->
**`jiuwenswarm/channels/browser/frontend/vite.config.ts`**

- 集成边界的导入/加载声明：`import { defineConfig } from "vite"`；`import { resolve } from "path"`；`import { cpSync, mkdirSync } from "fs"`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/vite.config.ts#L1-L54)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/vite.content.config.ts pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cf21833d47e98774e49688a556436779b488b04d748708b3b68e37d1093f0144 -->
**`jiuwenswarm/channels/browser/frontend/vite.content.config.ts`**

- 集成边界的导入/加载声明：`import { defineConfig } from "vite"`；`import { resolve } from "path"`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/vite.content.config.ts#L1-L35)。
<!-- /kb:file -->
