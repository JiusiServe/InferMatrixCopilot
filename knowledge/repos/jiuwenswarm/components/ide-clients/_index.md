---
title: "ide-clients"
created: 2026-10-01
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# ide-clients

理解该代码 owner 的职责、接口、配置与相关功能时查这里；通用审查方法不属于本目录。
- [VS Code 客户端 功能知识](feature-vscode.md)
- [JetBrains 客户端 功能知识](feature-jetbrains.md)
- [jetbrains-plugin](jetbrains-plugin/_index.md)
- [jetbrains-plugin-src](jetbrains-plugin-src/_index.md)
- [vscode-extension](vscode-extension/_index.md)
- [vscode-extension-src](vscode-extension-src/_index.md)
- [VS Code 客户端：实现深读](feature-depth-vscode.md)
- [JetBrains 客户端：实现深读](feature-depth-jetbrains.md)

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：ide clients。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| ide clients | 入口 | `jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/JiuwenSwarmService.kt`、`jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/ChatToolWindow.kt`、`jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts` |

- [JetBrains 插件（ide-clients）：架构、API、配置与行为](knowledge.md)
- [IDE 端代理文件编辑直接应用（DiffApplier）](feature-ide-file-edit-diff-apply.md)
- [IDE 单轮文件快照与回退（Rewind）](feature-ide-turn-rewind-snapshot.md)
- [shared-webview](shared-webview/_index.md)
