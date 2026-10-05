---
title: "tui-client"
created: 2026-10-01
updated: 2026-10-01
type: index
tags: [jiuwenswarm]
sources: []
---

# tui-client

理解该代码 owner 的职责、接口、配置与相关功能时查这里；通用审查方法不属于本目录。
- [TUI 对话与命令 功能知识](feature-tui.md)
- [已有 PR 自动修复功能知识](feature-autofix.md)
- [tui-client 源码接口与集成边界 01](source-contracts-01.md)
- [core](core/_index.md)
- [core-commands](core-commands/_index.md)
- [core-keybindings](core-keybindings/_index.md)
- [core-supervision](core-supervision/_index.md)
- [core-utils](core-utils/_index.md)
- [ui](ui/_index.md)
- [ui-components](ui-components/_index.md)
- [ui-rendering](ui-rendering/_index.md)
- [TUI 对话与命令：实现深读](feature-depth-tui.md)
- [已有 PR 自动修复：实现深读](feature-depth-autofix.md)

## 代码快速入口（Direct）
<!-- kb-init:quick-map -->

触发词：tui client。PR 描述或改动命中下表一行时，先读该行的规则，再读页面其余部分。

| PR 描述在做什么 | 精确规则 | 第一批 live 源码 |
|---|---|---|
| tui client | 入口 | `jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.ts`、`jiuwenswarm/channels/tui/frontend/src/core/commands/builtins/autofix-pr.watch.ts`、`jiuwenswarm/channels/tui/frontend/src/index.ts` |
