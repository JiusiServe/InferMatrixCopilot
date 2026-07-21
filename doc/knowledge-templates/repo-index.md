<!-- TEMPLATE: a repo entry index -> knowledge/repos/<repo>/_index.md.
     Fill <...>, link every topic/component/model dir below (one link each),
     add a row for <repo> in knowledge/repos/_index.md, then delete this comment. -->
---
title: "<Repo display name>"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: index
tags: [<tag-from-SCHEMA.md>]
sources: []
---

# <Repo display name>

- 上游仓库：`<owner>/<repo>`
- 常用分支：默认分支 `<main>`；<other branches>
- 适用范围：<what work this slice covers>
- 组件源码映射已按 `<repo> main @ <sha>` 校验

## 什么时候查这里

- 当前 Git 仓库或用户明确目标是 <repo>。

## 不放什么

- 跨仓库通用方法（放 `general/`）。
- 其他仓库的规则。

## 当前入口

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 开始任何 <repo> 修改、测试、发布任务 | [硬门禁](rules.md) | 仓库硬规则 |
| 查看共享代码模块 | [components](components/_index.md) | 模块职责地图 |
| 查看某个模型 | [models](models/_index.md) | 模型入口 |
