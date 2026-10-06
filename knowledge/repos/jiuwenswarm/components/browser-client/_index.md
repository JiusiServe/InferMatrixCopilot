---
title: "browser-client"
created: 2026-10-01
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# browser-client

理解该代码 owner 的职责、接口、配置与相关功能时查这里；通用审查方法不属于本目录。
- [Chromium 浏览器扩展 功能知识](feature-browser-client.md)
- [background](background/_index.md)
- [content](content/_index.md)
- [content-adapters](content-adapters/_index.md)
- [options](options/_index.md)
- [popup](popup/_index.md)
- [shared](shared/_index.md)
- [sidepanel](sidepanel/_index.md)
- [webview](webview/_index.md)
- [Chromium 浏览器扩展：实现深读](feature-depth-browser-client.md)

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：browser client。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| browser client | 入口 | `jiuwenswarm/channels/browser/frontend/src/background/index.ts`、`jiuwenswarm/channels/browser/frontend/src/sidepanel/index.ts`、`jiuwenswarm/channels/browser/` |

- [JiuwenSwarm browser-client（Chromium 扩展）背景服务与内容脚本](knowledge.md)
- [browser-client 源码接口与集成边界 01](source-contracts-01.md)
