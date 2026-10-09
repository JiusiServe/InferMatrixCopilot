---
title: "components-teamarea 审查规则"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [jiuwenswarm, components]
sources: ["PR #7584"]
confidence: high
---

# components-teamarea 审查规则

## JW-WEB-TAB-1a — 带内嵌关闭按钮的 tab 只处理自身键盘激活

- 触发：修改 ExpandedPanelTabs 的 role=tab 容器、CloseButton 或键盘事件委托。
- 强制：Enter/Space 的切页处理器先确认 event.target===event.currentTarget；来自内部按钮的键盘事件保留按钮原生激活，点击关闭不冒泡为切页。
- 禁止：父 tab 对内部关闭按钮的 keydown 调用 preventDefault 并切页；只处理鼠标 stopPropagation 而漏掉键盘路径。
- 验收：Tab 聚焦关闭按钮后 Enter 和 Space 均关闭目标页，不触发 onTabChange；聚焦 tab 自身仍可键盘切页。^[PR #7584]
