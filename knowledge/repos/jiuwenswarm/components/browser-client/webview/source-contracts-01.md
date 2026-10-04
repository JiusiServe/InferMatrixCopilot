---
title: "webview 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# webview 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/channels/browser/frontend/src/webview/chat.html pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5e9074cf842f021b335db14872e6ac0aaad654aab201c57ba4ba7cb80542fccc -->
**`jiuwenswarm/channels/browser/frontend/src/webview/chat.html`**

- 源码声明的类型、组件或调用边界：`vscodeApi`, `send`, `state`, `_historyPendingAssistant`, `_historyBuffer`, `handleHostMessage`, `inp`, `rewindBar`；这是词法声明索引，不把局部变量当成对外导出 API。
- 页面装配边界：body, script 标签；资源装载与宿主连接取决于对应属性和脚本实现。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/browser/frontend/src/webview/chat.html#L1-L4877)。
<!-- /kb:file -->
