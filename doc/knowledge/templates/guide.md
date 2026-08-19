<!-- 模板：方法 / how-to 页 —— 一套**不是**硬门禁的流程。
     按需拉取，所以可以比 rules.md 长；但仍然必须是可执行的，而不是叙述。
     路径：组件或模型 owner 根目录；工作主题集合可用 guides/。
     填掉 <...>，在最近的 _index.md 里注册，然后删掉本注释。 -->
---
title: "<Guide title>"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: guide
tags: [<tag-from-SCHEMA.md>]
sources: [<PR #NNNN>, <path/to/source.py>]
---

# <Guide title>

## 什么时候用

- <the observable condition that should bring a reader here>
- 不适用：<the neighbouring case that belongs to another page> → `<path>`

## 步骤 / 方法

1. <step — a command or an exact file to open, not "consider ...">
2. <step>

## 怎样验证

- <the check that proves the method worked>

## 已知失败模式

| 现象 | 原因 | 处理 |
|---|---|---|
| <symptom> | <cause> | <fix> |

<!-- 如果这一页开始堆积硬性的"必须/禁止"门禁，它们应该搬进 owner 的 rules.md ——
     guide 是你**选择**去读的，rule 是**无论你问没问都会加载**的。 -->
